from rest_framework import permissions


class IsModerator(permissions.BasePermission):
    """Пользователь входит в группу moderators."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.groups.filter(name='moderators').exists()
        )


class IsOwner(permissions.BasePermission):
    """Объект принадлежит текущему пользователю (obj.owner или obj == user)."""

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        return obj == request.user