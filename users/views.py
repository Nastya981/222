from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.shortcuts import redirect, render
from django.urls import reverse
from django.conf import settings

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from .models import User, Payment
from .serializers import UserSerializer, PaymentSerializer


class UserViewSet(viewsets.ModelViewSet):
    """CRUD для пользователей (дополнительное задание)"""
    queryset = User.objects.all()
    serializer_class = UserSerializer


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """Просмотр платежей текущего пользователя с фильтрацией и сортировкой"""
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ('course', 'lesson', 'payment_method')
    ordering_fields = ('payment_date', '-payment_date')

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)


def register(request):
    """Простая регистрация пользователя."""
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        if email and password:
            user = User.objects.create_user(email=email, password=password)
            user.is_active = False
            user.save()
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            activate_url = request.build_absolute_uri(
                reverse("users:activate", kwargs={"uidb64": uid, "token": token})
            )
            send_mail(
                subject="Активация аккаунта",
                message=f"Перейдите по ссылке: {activate_url}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )
            return redirect("users:login")
    return render(request, "users/form.html", {"title": "Регистрация"})


def activate(request, uidb64, token):
    """Активация пользователя по ссылке из письма."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return redirect("users:login")
    return render(request, "users/message.html", {"message": "Ссылка недействительна."})