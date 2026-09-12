from django.db.models import Count
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.claims.models import Claim

from .export_utils import build_items_pdf, build_items_xlsx
from .matching import rank_candidates
from .models import Item
from .permissions import IsReporterOrStaffOrReadOnly
from .serializers import ItemSerializer


class ItemViewSet(viewsets.ModelViewSet):
    serializer_class = ItemSerializer
    permission_classes = [IsReporterOrStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "title",
        "category",
        "color",
        "brand",
        "description",
        "location",
    ]
    ordering_fields = ["created_at", "event_date", "title"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = Item.objects.select_related("reporter").all()
        params = self.request.query_params

        report_type = params.get("report_type")
        item_status = params.get("status")
        category = params.get("category")
        location = params.get("location")
        mine = params.get("mine")

        if report_type:
            queryset = queryset.filter(report_type=report_type.upper())
        if item_status:
            queryset = queryset.filter(status=item_status.upper())
        if category:
            queryset = queryset.filter(category__iexact=category)
        if location:
            queryset = queryset.filter(location__icontains=location)
        if mine == "true" and self.request.user.is_authenticated:
            queryset = queryset.filter(reporter=self.request.user)

        return queryset

    def perform_create(self, serializer):
        item = serializer.save(reporter=self.request.user)
        try:
            from apps.notifications.services import notify_reviewers

            notify_reviewers(
                title=f"New {item.get_report_type_display()} report",
                message=(
                    f"{self.request.user.username} reported "
                    f"'{item.title}' at {item.location}."
                ),
                notification_type="ITEM",
                link=f"/items/{item.pk}",
            )
        except Exception:
            # Notifications must never prevent the core report operation.
            pass

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[IsAuthenticated],
    )
    def matches(self, request, pk=None):
        source = self.get_object()
        opposite = (
            Item.ReportType.FOUND
            if source.report_type == Item.ReportType.LOST
            else Item.ReportType.LOST
        )
        candidates = list(
            Item.objects.filter(
                report_type=opposite,
                status=Item.Status.ACTIVE,
            )
            .exclude(pk=source.pk)
            .select_related("reporter")[:200]
        )

        results = rank_candidates(source, candidates)
        return Response(
            [
                {
                    "item": ItemSerializer(
                        result.item,
                        context={"request": request},
                    ).data,
                    "score": result.score,
                    "explanation": result.explanation,
                }
                for result in results
            ]
        )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
    )
    def close(self, request, pk=None):
        item = self.get_object()
        if (
            item.reporter_id != request.user.id
            and not request.user.is_staff
            and getattr(request.user, "role", "") != "ADMIN"
        ):
            return Response(
                {"detail": "Only the reporter or an administrator can close it."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if item.status == Item.Status.RETURNED:
            return Response(
                {"detail": "Returned items are already finalized."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        item.status = Item.Status.CLOSED
        item.save(update_fields=["status", "updated_at"])
        return Response(
            ItemSerializer(item, context={"request": request}).data
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    queryset = Item.objects.all()
    claims = request.user.claims.all()

    data = {
        "lost_active": queryset.filter(
            report_type=Item.ReportType.LOST,
            status=Item.Status.ACTIVE,
        ).count(),
        "found_active": queryset.filter(
            report_type=Item.ReportType.FOUND,
            status=Item.Status.ACTIVE,
        ).count(),
        "claims_pending": (
            Claim.objects.filter(status=Claim.Status.SUBMITTED).count()
            if (
                request.user.is_staff
                or getattr(request.user, "role", "") in {"ADMIN", "FACULTY"}
            )
            else claims.filter(status=Claim.Status.SUBMITTED).count()
        ),
        "returned": queryset.filter(status=Item.Status.RETURNED).count(),
        "my_reports": queryset.filter(reporter=request.user).count(),
        "resolution_rate": 0,
    }

    total_closed = queryset.filter(
        status__in=[Item.Status.RETURNED, Item.Status.CLOSED]
    ).count()
    total = queryset.count()
    data["resolution_rate"] = (
        round((total_closed / total) * 100)
        if total
        else 0
    )
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def analytics(request):
    if not (
        request.user.is_staff
        or getattr(request.user, "role", "") in {"ADMIN", "FACULTY"}
    ):
        return Response(
            {"detail": "Analytics are available to authorized staff."},
            status=status.HTTP_403_FORBIDDEN,
        )

    category_counts = list(
        Item.objects.values("category")
        .annotate(count=Count("id"))
        .order_by("-count")[:8]
    )
    location_counts = list(
        Item.objects.values("location")
        .annotate(count=Count("id"))
        .order_by("-count")[:8]
    )
    return Response(
        {
            "by_category": category_counts,
            "by_location": location_counts,
            "generated_at": timezone.now(),
        }
    )


def _export_rows(queryset):
    rows = [
        [
            "Reference",
            "Type",
            "Title",
            "Category",
            "Color",
            "Location",
            "Date",
            "Status",
            "Reporter",
        ]
    ]
    for item in queryset.select_related("reporter"):
        rows.append(
            [
                item.reference_code,
                item.report_type,
                item.title,
                item.category,
                item.color,
                item.location,
                item.event_date.isoformat(),
                item.status,
                item.reporter.username,
            ]
        )
    return rows


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def export_items(request, file_format):
    queryset = Item.objects.all().order_by("-created_at")
    rows = _export_rows(queryset)

    if file_format == "pdf":
        response = HttpResponse(
            build_items_pdf(rows),
            content_type="application/pdf",
        )
        response["Content-Disposition"] = (
            'attachment; filename="trackit-items.pdf"'
        )
        return response

    if file_format == "xlsx":
        response = HttpResponse(
            build_items_xlsx(rows),
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )
        response["Content-Disposition"] = (
            'attachment; filename="trackit-items.xlsx"'
        )
        return response

    return Response(
        {"detail": "Supported formats are pdf and xlsx."},
        status=status.HTTP_400_BAD_REQUEST,
    )
