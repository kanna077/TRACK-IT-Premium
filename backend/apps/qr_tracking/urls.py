from django.urls import path

from .views import CompleteHandoverView

urlpatterns = [
    path(
        "<uuid:token>/complete/",
        CompleteHandoverView.as_view(),
        name="complete-handover",
    ),
]
