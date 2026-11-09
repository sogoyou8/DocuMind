"""D5 real read-only SQL indicators and audit. No mock KPI in public demo."""
from uuid import UUID

from django.conf import settings
from django.db import connection
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import AuditEvent, Document


class CurrencySummarySerializer(serializers.Serializer):
    currency = serializers.CharField()
    invoice_count = serializers.IntegerField()
    supplier_count = serializers.IntegerField()
    subtotal = serializers.DecimalField(max_digits=18, decimal_places=2)
    tax = serializers.DecimalField(max_digits=18, decimal_places=2)
    total = serializers.DecimalField(max_digits=18, decimal_places=2)


class MonthlySummarySerializer(serializers.Serializer):
    month = serializers.DateField()
    currency = serializers.CharField()
    invoice_count = serializers.IntegerField()
    total = serializers.DecimalField(max_digits=18, decimal_places=2)


class SupplierSummarySerializer(serializers.Serializer):
    supplier_name = serializers.CharField()
    currency = serializers.CharField()
    invoice_count = serializers.IntegerField()
    total = serializers.DecimalField(max_digits=18, decimal_places=2)


class StatusSummarySerializer(serializers.Serializer):
    state = serializers.CharField()
    count = serializers.IntegerField()


class IssueSummarySerializer(serializers.Serializer):
    code = serializers.CharField()
    severity = serializers.CharField()
    count = serializers.IntegerField()


class AnalyticsResponseSerializer(serializers.Serializer):
    available = serializers.BooleanField()
    reason = serializers.CharField(allow_null=True)
    currencies = CurrencySummarySerializer(many=True)
    monthly = MonthlySummarySerializer(many=True)
    suppliers = SupplierSummarySerializer(many=True)
    statuses = StatusSummarySerializer(many=True)
    issues = IssueSummarySerializer(many=True)


class AuditEntrySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    document_id = serializers.UUIDField()
    document_name = serializers.CharField()
    action = serializers.CharField()
    actor = serializers.CharField(allow_null=True)
    created_at = serializers.DateTimeField()


class AuditResponseSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    results = AuditEntrySerializer(many=True)


@extend_schema(
    request=None,
    responses={200: AnalyticsResponseSerializer},
    description="D5: vues SQL D3 sur factures validées uniquement ; réponse vide en démo.",
)
@api_view(["GET"])
@permission_classes([AllowAny])
def analytics(request):
    unavailable = {
        "available": False, "reason": "Analyse indisponible en démonstration publique.",
        "currencies": [], "monthly": [], "suppliers": [],
        "statuses": [], "issues": [],
    }
    if settings.DEMO_READONLY:
        return Response(unavailable)
    if not request.user.is_authenticated:
        raise PermissionDenied()
    if connection.vendor != "postgresql":
        return Response({**unavailable, "reason": "PostgreSQL local requis."}, status=503)

    def unpack(columns, data):
        return [dict(zip(columns, row)) for row in data]

    with connection.cursor() as cur:
        cur.execute("SELECT currency, invoice_count, supplier_count, subtotal, tax, total "
                    "FROM bi.currency_totals ORDER BY currency")
        currencies = unpack(
            ("currency", "invoice_count", "supplier_count", "subtotal", "tax", "total"),
            cur.fetchall(),
        )
        cur.execute("SELECT month, currency, invoice_count, total "
                    "FROM bi.spending_monthly ORDER BY month, currency")
        monthly = unpack(("month", "currency", "invoice_count", "total"), cur.fetchall())
        cur.execute("SELECT supplier_name, currency, invoice_count, total "
                    "FROM bi.spending_suppliers ORDER BY total DESC, supplier_name LIMIT 20")
        suppliers = unpack(("supplier_name", "currency", "invoice_count", "total"), cur.fetchall())
        cur.execute("SELECT document_state, SUM(document_count)::integer "
                    "FROM bi.document_status_counts GROUP BY document_state "
                    "ORDER BY document_state")
        statuses = [{"state": state, "count": count} for state, count in cur.fetchall()]
        cur.execute("SELECT issue_code, severity, issue_count "
                    "FROM bi.issue_code_counts ORDER BY issue_count DESC, issue_code LIMIT 20")
        issues = [
            {"code": code, "severity": severity, "count": count}
            for code, severity, count in cur.fetchall()
        ]
    payload = {
        "available": True, "reason": None, "currencies": currencies,
        "monthly": monthly, "suppliers": suppliers,
        "statuses": statuses, "issues": issues,
    }
    return Response(AnalyticsResponseSerializer(payload).data)


@extend_schema(
    request=None,
    responses={200: AuditResponseSerializer},
    description="D5: historique des décisions documentaires sans chemin de fichier privé.",
)
@api_view(["GET"])
@permission_classes([AllowAny])
def audit(request):
    if settings.DEMO_READONLY:
        return Response({"count": 0, "results": []})
    if not request.user.is_authenticated:
        raise PermissionDenied()
    query = AuditEvent.objects.select_related("document", "actor").filter(
        document__source=Document.Source.UPLOAD,
    )
    doc_id = request.query_params.get("document")
    if doc_id:
        try:
            query = query.filter(document_id=UUID(doc_id))
        except (ValueError, TypeError, AttributeError) as exc:
            raise ValidationError({"document": "UUID attendu."}) from exc
    count = query.count()
    events = query.order_by("-created_at")[:40]
    return Response({
        "count": count,
        "results": [{
            "id": event.id,
            "document_id": event.document_id,
            "document_name": event.document.original_name,
            "action": event.action,
            "actor": event.actor.username if event.actor else None,
            "created_at": event.created_at,
        } for event in events],
    })
