from datetime import datetime
from functools import wraps

from django.http import JsonResponse
from django.shortcuts import redirect
from rest_framework.authtoken.models import Token
from rest_framework.permissions import BasePermission


# ===========================================================================
# Existing decorators (kept, cleaned up)
# ===========================================================================

def check_token_in_session(view_func):
    """Check user is logged in via session token (Django views only)."""
    @wraps(view_func)
    def wrapper_view(request, *args, **kwargs):
        token = request.session.get('token')
        if token:
            return view_func(request, *args, **kwargs)
        return redirect('login_view')
    return wrapper_view


def otp_required(view_func):
    """Check OTP has been validated in session (Django views only)."""
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.session.get("pin"):
            return redirect('login_view')
        response = view_func(request, *args, **kwargs)
        if response is None:
            return redirect('login_view')
        return response
    return wrapped_view


def session_timeout(view_func):
    """
    Invalidate session after 30 minutes of inactivity (Django views only).
    """
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        user = request.session.get('user_id')
        if user:
            now = datetime.now()
            last_activity = request.session.get('last_activity')
            if last_activity:
                last_activity_time = datetime.strptime(
                    last_activity, '%Y-%m-%d %H:%M:%S.%f'
                )
                if (now - last_activity_time).seconds > 30 * 60:
                    request.session.flush()
                    return redirect('login_view')
            request.session['last_activity'] = now.strftime('%Y-%m-%d %H:%M:%S.%f')
        return view_func(request, *args, **kwargs)
    return wrapped_view


# ===========================================================================
# NEW — DRF Permission Classes (used on API views with @permission_classes)
# ===========================================================================

def _get_role(request):
    """
    Helper: safely fetch the UserRole for the authenticated request user.
    Returns None if the user has no role assigned.
    """
    try:
        return request.user.role
    except Exception:
        return None


class IsActiveBank(BasePermission):
    """
    Allows access only if the authenticated user is linked to an active Bank.
    Use this as the baseline permission on all bank-facing API views.

    Usage:
        @permission_classes([IsAuthenticated, IsActiveBank])
    """
    message = "Your bank account is inactive or not configured."

    def has_permission(self, request, view):
        try:
            return request.user.bank.is_active
        except Exception:
            return False


class IsAnalystOrAbove(BasePermission):
    """
    Allows ANALYST, INSTITUTION_ADMIN, SUPER_ADMIN.
    Use on upload and reconciliation views.

    Usage:
        @permission_classes([IsAuthenticated, IsAnalystOrAbove])
    """
    message = "Analyst role or above required."

    def has_permission(self, request, view):
        role = _get_role(request)
        if role is None:
            return False
        return role.can_upload()


class IsAuditorOrAbove(BasePermission):
    """
    Allows AUDITOR, ANALYST, INSTITUTION_ADMIN, SUPER_ADMIN.
    Use on export and report views.

    Usage:
        @permission_classes([IsAuthenticated, IsAuditorOrAbove])
    """
    message = "Auditor role or above required."

    def has_permission(self, request, view):
        role = _get_role(request)
        if role is None:
            return False
        return role.can_export()


class IsInstitutionAdmin(BasePermission):
    """
    Allows INSTITUTION_ADMIN and SUPER_ADMIN only.
    Use on user management and ISO rule configuration views.

    Usage:
        @permission_classes([IsAuthenticated, IsInstitutionAdmin])
    """
    message = "Institution Admin role required."

    def has_permission(self, request, view):
        role = _get_role(request)
        if role is None:
            return False
        return role.is_institution_admin()


class IsSuperAdmin(BasePermission):
    """
    Allows SUPER_ADMIN only (you — Titus).
    Use on cross-bank admin views.

    Usage:
        @permission_classes([IsAuthenticated, IsSuperAdmin])
    """
    message = "Super Admin access required."

    def has_permission(self, request, view):
        role = _get_role(request)
        if role is None:
            return False
        return role.is_super_admin()


class IsSameBankOrSuperAdmin(BasePermission):
    """
    Object-level permission: allows access only if the object belongs
    to the user's bank, OR the user is a SUPER_ADMIN.
    Use with get_object() views (detail endpoints).

    Usage:
        @permission_classes([IsAuthenticated, IsSameBankOrSuperAdmin])
        ...
        self.check_object_permissions(request, obj)
    """
    message = "You do not have access to this bank's data."

    def has_permission(self, request, view):
        # Allow through to object-level check
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        role = _get_role(request)
        if role is None:
            return False
        if role.is_super_admin():
            return True
        # obj must have a .bank attribute
        try:
            return obj.bank == request.user.bank
        except Exception:
            return False
