from django.conf import settings
from django.db import connection, IntegrityError
from django.shortcuts import render
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Document
from .permissions import DocumentPermission
from .serializers import DocumentReadSerializer, DocumentCreateSerializer

def home(request):
    return render(request, "index.html", {"demo": settings.DEMO_READONLY})

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

@api_view(["GET"])
@permission_classes([AllowAny])
def overview(request):
    if not settings.DEMO_READONLY and not request.user.is_authenticated:
        raise PermissionDenied()
    records = Document.objects.all()
    return Response({
        "mode": "synthetic-demo" if settings.DEMO_READONLY else "local",
        "total": records.count(),
        "received": records.filter(state=Document.State.RECEIVED).count(),
        "rejected": records.filter(state=Document.State.REJECTED).count(),
        "processed": records.filter(state__in=[
            Document.State.ACCEPTED, Document.State.INDEXED
        ]).count(),
        "airflow_enabled": False,
        "ai_enabled": False,
        "note": "D1 metadata only; no actual PDF extraction or AI.",
    })

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    permission_classes = [DocumentPermission]
    http_method_names = ["get", "post", "head", "options"]

    def get_serializer_class(self):
        return DocumentCreateSerializer if self.action == "create" else DocumentReadSerializer

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
