from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    UserViewSet,
    UserCreateAPIView,
    MyTokenObtainPairView,
    MyTokenRefreshView,
)

app_name = 'users'

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # JWT
    path('api/login/', MyTokenObtainPairView.as_view(), name='login'),
    path('api/token/refresh/', MyTokenRefreshView.as_view(), name='token-refresh'),

    # Регистрация
    path('api/register/', UserCreateAPIView.as_view(), name='register'),

    # ViewSet
    path('', include(router.urls)),
]