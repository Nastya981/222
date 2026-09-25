from django.contrib.auth import views as auth_views
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from users import views
from users.views import UserViewSet, PaymentViewSet

app_name = "users"

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'payments', PaymentViewSet, basename='payment')

urlpatterns = [
    path("", include(router.urls)),
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
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="users/form.html",
            email_template_name="users/password_reset_email.txt",
            success_url="/accounts/password-reset/done/",
            extra_context={"title": "Восстановление пароля"},
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="users/message.html",
            extra_context={"message": "Письмо для восстановления отправлено."},
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="users/form.html",
            success_url="/accounts/reset/done/",
            extra_context={"title": "Новый пароль"},
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="users/message.html",
            extra_context={"message": "Пароль успешно изменён."},
        ),
        name="password_reset_complete",
    ),
]