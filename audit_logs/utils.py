"""
Helper to create audit log entries from views/signals.
"""
from .models import AuditLog


def log_action(request, action, message="", user=None):
    """
    Record an audit log entry. user defaults to request.user if request is provided.
    """
    actor = user
    if request and actor is None and hasattr(request, "user"):
        actor = request.user
    ip = None
    if request and hasattr(request, "META"):
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            ip = xff.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
    AuditLog.objects.create(
        user=actor,
        action=action,
        message=message or "",
        ip_address=ip,
    )
