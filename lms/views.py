from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated

from .models import Course, Lesson
from .serializers import CourseSerializer, LessonSerializer
from .permissions import IsModerator, IsOwner, NotModerator, ModeratorOrOwner


class CourseViewSet(viewsets.ModelViewSet):
    """CRUD для курсов через ViewSet. Права по action."""
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), NotModerator()]
        if self.action in ['update', 'partial_update']:
            return [IsAuthenticated(), ModeratorOrOwner()]
        if self.action == 'destroy':
            return [IsAuthenticated(), IsOwner()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class LessonListCreateView(generics.ListCreateAPIView):
    """Список уроков и создание."""
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), NotModerator()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class LessonRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """Получение, обновление, удаление урока."""
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH']:
            return [IsAuthenticated(), ModeratorOrOwner()]
        if self.request.method == 'DELETE':
            return [IsAuthenticated(), IsOwner()]
        return [IsAuthenticated()]