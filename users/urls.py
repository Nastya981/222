from django.contrib.auth import views as auth_views
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from users import views
from users.views import (
    UserViewSet,
    PaymentViewSet,
    MyTokenObtainPairView,
    MyTokenRefreshView,
    UserCreateAPIView,
    PaymentCreateAPIView,
    PaymentStatusAPIView,
)

app_name = "users"

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'payments', PaymentViewSet, basename='payment')

urlpatterns = [
    # Специфичные пути ДО include(router.urls)
    path("payments/create/", PaymentCreateAPIView.as_view(), name="payment-create"),
    path("payments/<int:pk>/status/", PaymentStatusAPIView.as_view(), name="payment-status"),

    # JWT
    path("api/login/", MyTokenObtainPairView.as_view(), name="api-login"),
    path("api/token/refresh/", MyTokenRefreshView.as_view(), name="api-token-refresh"),

    # API-регистрация
    path("api/register/", UserCreateAPIView.as_view(), name="api-register"),

    # HTML-регистрация и активация
    path("register/", views.register, name="register"),
    path("activate/<uidb64>/<token>/", views.activate, name="activate"),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="users/form.html",
            extra_context={"title": "Вход"},
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # Роутер — в конце
    path("", include(router.urls)),
]