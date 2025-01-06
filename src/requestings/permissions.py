from django.db.models import Q

from rest_framework import permissions

from requestings.models import RequestingHistory


class IsParticipatedRequesting(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        request_id = view.kwargs.get('id')

        requesting = RequestingHistory.objects.filter(
            Q(pk=request_id)& \
            (
                Q(client=user)| \
                Q(agent=user)| \
                Q(deliverer=user)
            )
        ).first()

        if requesting == None:
            return False

        return True

    def has_object_permission(self, request, view, obj):
        user = request.user
        request_id = view.kwargs.get('id')

        requesting = RequestingHistory.objects.filter(
            Q(pk=request_id)& \
            (
                Q(client=user)| \
                Q(agent=user)| \
                Q(deliverer=user)
            )
        ).first()

        if requesting == None:
            return False

        return True
