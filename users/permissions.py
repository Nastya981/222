from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """Пользователь может редактировать/удалять только свой профиль."""

    def has_object_permission(self, request, view, obj):
        return obj == request.user