from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from documents.api import home

urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("api/v1/", include("documents.urls")),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="api-docs"),
]
