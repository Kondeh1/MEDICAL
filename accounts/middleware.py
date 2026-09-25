"""
Middleware for accounts app:
- RedirectAdminToAppDashboardMiddleware: Redirects admins from Django admin to app dashboard
- OnlineStatusMiddleware: Tracks user online status and last seen timestamp
"""
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class RedirectAdminToAppDashboardMiddleware:
    """
    - Unauthenticated users visiting /admin/ are sent to our login page.
    - Authenticated administrators visiting /admin/ or /admin (index only) are redirected to app dashboard.
    - Admins CAN access /admin/accounts/..., /admin/auth/... etc. when clicking Manage users, Provider profiles.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith("/admin"):
            return self.get_response(request)

        # Strip trailing slash for comparison; /admin and /admin/ are the index
        path = request.path.rstrip("/") or "/"
        is_admin_index = path == "/admin"

        # Allow Django admin sub-pages (Manage users, Provider profiles, etc.)
        if not is_admin_index:
            return self.get_response(request)

        # Allow admin index when explicitly requested via ?django=1 (Django admin button)
        if request.GET.get("django") == "1":
            return self.get_response(request)

        if request.user.is_authenticated:
            if hasattr(request.user, "is_administrator") and request.user.is_administrator:
                return redirect(reverse("dashboard:admin_dashboard"))
        else:
            login_url = reverse(settings.LOGIN_URL)
            return redirect(f"{login_url}?next={reverse('dashboard:admin_dashboard')}")

        return self.get_response(request)


class OnlineStatusMiddleware:
    """Middleware to update user last_seen timestamp on each request."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Update last_seen for authenticated users
        if request.user.is_authenticated:
            # Only update if last_seen is older than 1 minute (to reduce DB writes)
            if (not request.user.last_seen or 
                timezone.now() - request.user.last_seen > timedelta(minutes=1)):
                request.user.update_last_seen()
        
        response = self.get_response(request)
        return response
