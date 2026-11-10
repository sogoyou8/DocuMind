from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .api import (
    DocumentViewSet, ProcessingRunViewSet, ExtractedRecordViewSet,
    QualityIssueViewSet, InvoiceViewSet, health, overview,
)

from .assistant_api import ask, assistant_status
from .frontend_api import analytics, audit
from .session_views import session_status, session_login, session_logout

router = DefaultRouter()
router.register("documents", DocumentViewSet, basename="documents")
router.register("processing-runs", ProcessingRunViewSet, basename="processing-runs")
router.register("records", ExtractedRecordViewSet, basename="records")
router.register("quality-issues", QualityIssueViewSet, basename="quality-issues")
router.register("invoices", InvoiceViewSet, basename="invoices")
urlpatterns = [
    path("health/", health, name="health"),
    path("overview/", overview, name="overview"),
    path("analytics/", analytics, name="analytics"),
    path("audit/", audit, name="audit"),
    path("session/", session_status, name="session-status"),
    path("session/login/", session_login, name="session-login"),
    path("session/logout/", session_logout, name="session-logout"),
    path("assistant/ask/", ask, name="assistant-ask"),
    path("assistant/status/", assistant_status, name="assistant-status"),
    path("", include(router.urls)),
]
