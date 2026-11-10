from django.conf import settings
from django.db import connection, IntegrityError
from django.shortcuts import render
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Document, ProcessingRun, ExtractedRecord, QualityIssue, Invoice
from .permissions import DocumentPermission
from drf_spectacular.utils import extend_schema
from .serializers import (
    DocumentReadSerializer, DocumentCreateSerializer,
    HealthResponseSerializer, HealthUnavailableSerializer, OverviewResponseSerializer,
    ProcessOptionsSerializer, ProcessResultSerializer,
    ProcessingRunSerializer, ExtractedRecordSerializer,
    QualityIssueSerializer, InvoiceSerializer,
    AskDocumentSerializer, AssistantAnswerSerializer,
    AssistantStatusSerializer, IndexResultSerializer,
)

def home(request):
    return render(request, "index.html", {"demo": settings.DEMO_READONLY})

@extend_schema(
    request=None,
    responses={200: HealthResponseSerializer, 503: HealthUnavailableSerializer},
    description="Vérifie la disponibilité de la base sans révéler les paramètres internes.",
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return Response({"status": "unavailable"}, status=503)
    return Response({"status": "ok", "service": "documind-d1"})

@extend_schema(
    request=None,
    responses={200: OverviewResponseSerializer},
    description="Compteurs D1 sur les métadonnées ; pas de pipeline ou IA exécutés.",
)
@api_view(["GET"])
@permission_classes([AllowAny])
def overview(request):
    if not settings.DEMO_READONLY and not request.user.is_authenticated:
        raise PermissionDenied()
    records = (Document.objects.filter(source=Document.Source.DEMO)
               if settings.DEMO_READONLY else Document.objects.all())
    return Response({
        "mode": "synthetic-demo" if settings.DEMO_READONLY else "local",
        "total": records.count(),
        "received": records.filter(state=Document.State.RECEIVED).count(),
        "rejected": records.filter(state=Document.State.REJECTED).count(),
        "processed": records.filter(state__in=[
            Document.State.ACCEPTED, Document.State.INDEXED
        ]).count(),
        "airflow_enabled": False,
        "ai_enabled": bool(settings.DOCUMIND_AI_ENABLED and not settings.DEMO_READONLY),
        "note": "Render: fictional D1 metadata only. Local D2/D3 and optional D4 service.",
    })

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    permission_classes = [DocumentPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        if settings.DEMO_READONLY:
            return qs.filter(source=Document.Source.DEMO)
        return qs
    http_method_names = ["get", "post", "head", "options"]

    def get_serializer_class(self):
        if self.action == "create":
            return DocumentCreateSerializer
        if self.action == "process":
            return ProcessOptionsSerializer
        return DocumentReadSerializer

    def create(self, request, *args, **kwargs):
        if settings.DEMO_READONLY:
            raise PermissionDenied("La démo gratuite est en lecture seule.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            doc = serializer.save()
        except IntegrityError:
            raise ValidationError({"file": "Document déjà présent."})
        return Response(DocumentReadSerializer(doc).data, status=status.HTTP_201_CREATED)


    @extend_schema(
        request=None,
        responses={200: IndexResultSerializer},
        description="D4 local uniquement : indexe un document D2 valide vers Chroma/Ollama. "
                    "Requiert rôle opérateur/admin, interdit sur Render.",
    )
    @action(detail=True, methods=["post"], url_path="index")
    def index(self, request, pk=None):
        from .rag.security import require_d4
        require_d4()
        document = self.get_object()
        from .rag.indexer import index_document, IndexNotAllowed
        from .rag.ollama import LocalModelUnavailable
        try:
            result = index_document(document.id)
        except IndexNotAllowed as exc:
            raise ValidationError({"document": str(exc)}) from exc
        except LocalModelUnavailable as exc:
            return Response({"detail": str(exc)}, status=503)
        return Response(result)

    @extend_schema(
        request=ProcessOptionsSerializer,
        responses={200: ProcessResultSerializer},
        description="D2 local : traitement idempotent d'un document importé, force=true pour rejouer.",
    )
    @action(detail=True, methods=["post"], url_path="process")
    def process(self, request, pk=None):
        from .pipeline.runner import process_document, ProcessingNotAllowed

        opts = ProcessOptionsSerializer(data=request.data)
        opts.is_valid(raise_exception=True)
        document = self.get_object()
        try:
            run, skipped = process_document(
                document.id, force=opts.validated_data["force"], actor=request.user
            )
        except ProcessingNotAllowed as exc:
            raise ValidationError({"document": str(exc)}) from exc
        return Response({
            "run_id": run.id,
            "status": run.status,
            "attempt_number": run.attempt_number,
            "skipped": skipped,
            "records_count": run.records.count(),
            "issues_count": run.issues.count(),
            "invoices_count": run.invoices.count(),
        })


class _D2ReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [DocumentPermission]
    document_filter = "document_id"

    def get_queryset(self):
        # The public demo has *no* D2 processing, even if its DB is populated
        # accidentally: only synthetic D1 document metadata are public.
        qs = super().get_queryset()
        if settings.DEMO_READONLY:
            return qs.none()
        document_id = self.request.query_params.get("document")
        if document_id:
            from uuid import UUID
            try:
                document_id = UUID(document_id)
            except (ValueError, AttributeError) as exc:
                raise ValidationError({"document": "UUID attendu."}) from exc
            qs = qs.filter(**{self.document_filter: document_id})
        return qs


class ProcessingRunViewSet(_D2ReadOnlyViewSet):
    queryset = ProcessingRun.objects.select_related("document").all()
    serializer_class = ProcessingRunSerializer


class ExtractedRecordViewSet(_D2ReadOnlyViewSet):
    queryset = ExtractedRecord.objects.select_related("document", "run").all()
    serializer_class = ExtractedRecordSerializer


class QualityIssueViewSet(_D2ReadOnlyViewSet):
    queryset = QualityIssue.objects.select_related("record", "run").all()
    serializer_class = QualityIssueSerializer
    document_filter = "run__document_id"


class InvoiceViewSet(_D2ReadOnlyViewSet):
    queryset = Invoice.objects.select_related("supplier", "record", "document", "run").all()
    serializer_class = InvoiceSerializer
