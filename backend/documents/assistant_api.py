"""Local-only, authenticated, rate-limited document QA endpoints."""
from django.conf import settings
from django.core.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.exceptions import ValidationError

from .rag.security import require_d4
from .serializers import (
    AskDocumentSerializer, AssistantAnswerSerializer, AssistantStatusSerializer,
)


class RagThrottle(UserRateThrottle):
    scope = "rag"


@extend_schema(
    methods=["POST"],
    request=AskDocumentSerializer,
    responses={200: AssistantAnswerSerializer},
    description="D4: RAG documentaire local et sourcé. Aucun cloud; abstention "
                "en cas de preuve insuffisante; authentification obligatoire.",
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([RagThrottle])
def ask(request):
    require_d4()
    serializer = AskDocumentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    from .rag.graph import answer_question
    from .rag.ollama import LocalModelUnavailable
    try:
        reply = answer_question(serializer.validated_data["question"])
    except LocalModelUnavailable as exc:
        return Response({"detail": str(exc)}, status=503)
    except ValueError as exc:
        raise ValidationError({"question": str(exc)}) from exc
    return Response(reply)


@extend_schema(
    methods=["GET"],
    request=None,
    responses={200: AssistantStatusSerializer},
    description="D4 local : paramètres et nombre de passages, sans secrets.",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def assistant_status(request):
    require_d4()
    from .rag.ollama import LocalOllama
    from .rag.store import collection
    try:
        model = LocalOllama()
        chunks = collection().count()
    except Exception:
        return Response({"detail": "Index Chroma local indisponible."}, status=503)
    return Response({
        "mode": "local-only", "enabled": True,
        "embedding_model": model.embed_model, "generation_model": model.chat_model,
        "indexed_chunks": chunks,
    })
