from rest_framework import permissions


class IsOnlyForGuest(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if hasattr(user, 'agent_profile') or hasattr(user, 'dealer_profile'):
            return False

        return True

    def has_object_permission(self, request, view, obj):
        user = request.user

        if hasattr(user, 'agent_profile') or hasattr(user, 'dealer_profile'):
            return False

        return True


class IsOnlyForAgent(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if hasattr(user, 'agent_profile'):
            return True

    def has_object_permission(self, request, view, obj):
        user = request.user

        if hasattr(user, 'agent_profile'):
            return True


class IsOnlyForDealer(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if hasattr(user, 'dealer_profile'):
            return True

    def has_object_permission(self, request, view, obj):
        user = request.user

        if hasattr(user, 'dealer_profile'):
            return True


class IsOnlyControlRoomUser(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user

        return user.is_superuser

    def has_object_permission(self, request, view, obj):
        user = request.user

        return user.is_superuser


class IsOnlyDaangnAPIUser(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user

        return not user.is_anonymous and user.api_usage_type == 'DAANGN'

    def has_object_permission(self, request, view, obj):
        user = request.user

        return not user.is_anonymous and user.api_usage_type == 'DAANGN'
