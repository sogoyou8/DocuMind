from django.conf import settings
from rest_framework.permissions import BasePermission, SAFE_METHODS

class DocumentPermission(BasePermission):
    """Public demo can read only artificial metadata; local uploads require operator."""
    def has_permission(self, request, view):
        if settings.DEMO_READONLY:
            return request.method in SAFE_METHODS
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_staff or request.user.groups.filter(
            name="documind_operator").exists()
