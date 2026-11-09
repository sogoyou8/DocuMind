"""Hard boundaries for local-only D4 and untrusted uploaded text."""
import re
from django.conf import settings
from django.core.exceptions import PermissionDenied

INJECTION = re.compile(
    r"(?:ignore\s+(?:all\s+)?(?:previous|above|system)\s+instructions|"
    r"ignorez?\s+(?:les\s+)?instructions|"
    r"(?:system|developer|assistant)\s*:\s*(?:ignore|you\s+must|override)|"
    r"(?:reveal|print|show|disclose|envoie|affiche)\s+(?:the\s+)?"
    r"(?:api[\s_-]?key|secret|password|mot\s+de\s+passe)|"
    r"(?:curl|wget)\s+https?://|"
    r"(?:execute|ex[eé]cute)\s+(?:shell|commande|command))",
    flags=re.IGNORECASE,
)


def require_d4():
    if settings.DEMO_READONLY or not getattr(settings, "DOCUMIND_AI_ENABLED", False):
        raise PermissionDenied("Assistant IA local désactivé sur cette instance.")
    # The public Render SQLite demonstration can never process D4, even if
    # someone accidentally enables the feature flag.
    from django.db import connection
    if connection.vendor != "postgresql":
        raise PermissionDenied("L'index IA nécessite PostgreSQL local.")


def hostile_instruction(text: str) -> bool:
    """Conservative detection only, not a guarantee against all prompt injections."""
    return bool(INJECTION.search(text))


def safe_excerpt(value: str, limit: int = 420) -> str:
    return value.replace("\x00", "").strip()[:limit]
