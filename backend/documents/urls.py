from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .api import DocumentViewSet, health, overview

router = DefaultRouter()
router.register("documents", DocumentViewSet, basename="documents")
urlpatterns = [
    path("health/", health, name="health"),
    path("overview/", overview, name="overview"),
    path("", include(router.urls)),
]
