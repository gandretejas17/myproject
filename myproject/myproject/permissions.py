from rest_framework.permissions import BasePermission
from django.core.exceptions import PermissionDenied
from django.conf import settings
from utility.constants import SUPERUSER_ROLE

def is_model_permission(request, code_name):
    try:
        if not request.user.group:
            return False
        permissions = request.user.group.permissions.filter(codename=code_name)
        if permissions:
            return True
        else:
            return False
    except Exception:
        return False

class is_super_admin(BasePermission):
    """
    check for super admin login or not
    """
    def has_permission(self, request, view):
        try:
            return request.user.group_id == settings.GRP_SUPER_ADMIN
        except Exception:
            return False


class is_access(BasePermission):
    def has_permission(self, request, view):
        headers = settings.HEADERS
        # return request.META.get('HTTP_ACCESS_KEY') == headers
        return True

def is_super_user(f):
    def validate(self, request, *args, **kwargs):
        if request.user.role_id != SUPERUSER_ROLE:
            raise PermissionDenied

        return f(self, request, *args, **kwargs)
    return validate


def have_permission(request, role)-> bool: 
    return True if request.user.role_id == role else False




