from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ClaimMessageViewSet

router = DefaultRouter()
router.register("", ClaimMessageViewSet, basename="claim-message")

urlpatterns = [path("", include(router.urls))]
