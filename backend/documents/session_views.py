"""Browser session for local React. Never authorize writes in Render demo."""
import json

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST


def _operator(user):
    return bool(user.is_authenticated and (
        user.is_staff or user.groups.filter(name="documind_operator").exists()
    ))


@require_GET
@ensure_csrf_cookie
def session_status(request):
    user = request.user
    active = bool(user.is_authenticated and not settings.DEMO_READONLY)
    return JsonResponse({
        "mode": "synthetic-demo" if settings.DEMO_READONLY else "local",
        "authenticated": active,
        "username": user.get_username() if active else None,
        "operator": _operator(user) if active else False,
        "ai_enabled": bool(settings.DOCUMIND_AI_ENABLED and active),
        "csrf_token": get_token(request),
    })


@require_POST
@csrf_protect
def session_login(request):
    if settings.DEMO_READONLY:
        return JsonResponse({"detail": "La démo publique est en lecture seule."}, status=403)
    if len(request.body) > 2048:
        return JsonResponse({"detail": "Corps trop volumineux."}, status=400)
    try:
        body = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"detail": "JSON invalide."}, status=400)
    if not isinstance(body, dict):
        return JsonResponse({"detail": "JSON invalide."}, status=400)
    username, password = body.get("username", ""), body.get("password", "")
    if (not isinstance(username, str) or not isinstance(password, str)
            or not 1 <= len(username) <= 150 or not 1 <= len(password) <= 256):
        return JsonResponse({"detail": "Identifiants invalides."}, status=400)
    user = authenticate(request, username=username, password=password)
    if user is None or not user.is_active:
        return JsonResponse({"detail": "Identifiants incorrects."}, status=401)
    login(request, user)
    return JsonResponse({"authenticated": True, "username": user.get_username(),
                         "operator": _operator(user), "ai_enabled": settings.DOCUMIND_AI_ENABLED})


@require_POST
@csrf_protect
def session_logout(request):
    logout(request)
    return JsonResponse({"authenticated": False})
