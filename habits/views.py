from rest_framework import viewsets, permissions, mixins

from .models import Habit
from .serializers import HabitSerializer
from .paginators import HabitPagination
from .permissions import IsOwner


class HabitViewSet(viewsets.ModelViewSet):
    """
    CRUD для привычек.
    - list: свои + публичные
    - create/update/destroy: только свои
    """
    serializer_class = HabitSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = HabitPagination

    def get_queryset(self):
        user = self.request.user
        # свои привычки + публичные
        return Habit.objects.filter(user=user) | Habit.objects.filter(is_public=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsOwner()]
        return [permissions.IsAuthenticated()]


class PublicHabitViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Только чтение публичных привычек."""
    serializer_class = HabitSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = HabitPagination
    queryset = Habit.objects.filter(is_public=True)