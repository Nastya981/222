from rest_framework import viewsets, generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import User
from .serializers import UserSerializer, UserCreateSerializer
from .permissions import IsOwner


class MyTokenObtainPairView(TokenObtainPairView):
    """JWT-логин. POST /api/users/api/login/ {email, password}."""
    permission_classes = [permissions.AllowAny]


class MyTokenRefreshView(TokenRefreshView):
    """Обновление access-токена."""
    permission_classes = [permissions.AllowAny]


class UserCreateAPIView(generics.CreateAPIView):
    """Регистрация через API. POST /api/users/api/register/."""
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]


class UserViewSet(viewsets.ModelViewSet):
    """
    CRUD для пользователей.
    - create — открыт (регистрация)
    - update/destroy — только свой профиль
    - retrieve — свой профиль полностью
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsOwner()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return User.objects.filter(pk=self.request.user.pk)
        return User.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer