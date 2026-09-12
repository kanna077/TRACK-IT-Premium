from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ItemViewSet,
    analytics,
    dashboard_stats,
    export_items,
)

router = DefaultRouter()
router.register("", ItemViewSet, basename="item")

urlpatterns = [
    path("dashboard/", dashboard_stats),
    path("analytics/", analytics),
    path("export/<str:file_format>/", export_items),
    path("", include(router.urls)),
]
