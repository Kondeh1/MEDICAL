"""
Admin-only list and filter of audit logs.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import render
from django.views.generic import View

from accounts.mixins import AdminRequiredMixin
from .models import AuditLog


class AuditLogListView(AdminRequiredMixin, View):
    """Paginated list of audit log entries; optional filter by action."""

    def get(self, request):
        qs = AuditLog.objects.select_related("user").all()
        action = request.GET.get("action")
        if action:
            qs = qs.filter(action=action)
        paginator = Paginator(qs, 50)
        page = request.GET.get("page", 1)
        page_obj = paginator.get_page(page)
        return render(
            request,
            "audit_logs/list.html",
            {
                "page_obj": page_obj,
                "action_filter": action,
                "audit_actions": AuditLog.Action.choices,
            },
        )
