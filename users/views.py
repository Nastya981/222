from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.conf import settings
from django.utils import timezone

from rest_framework import viewsets, generics, permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from .models import User, Payment
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    PublicUserSerializer,
    PrivateUserSerializer,
    PaymentSerializer,
    PaymentCreateSerializer,
)
from .permissions import IsOwner
from . import services


# ============================================================
# JWT — открытые эндпоинты
# ============================================================

class MyTokenObtainPairView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]


class MyTokenRefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]


# ============================================================
# API-регистрация (JSON)
# ============================================================

class UserCreateAPIView(generics.CreateAPIView):
    """Регистрация нового пользователя через API."""
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]


# ============================================================
# CRUD пользователей (ViewSet)
# ============================================================

class UserViewSet(viewsets.ModelViewSet):
    """
    CRUD для пользователей.
    - create — открыт
    - retrieve — свой профиль полностью, чужой — публично
    - update/destroy — только свой профиль
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
        if self.action == 'retrieve':
            if self.kwargs.get('pk') == str(self.request.user.pk):
                return PrivateUserSerializer
            return PublicUserSerializer
        return UserSerializer


# ============================================================
# Платежи
# ============================================================

class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """Просмотр платежей текущего пользователя с фильтрацией и сортировкой."""
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ('course', 'lesson', 'payment_method')
    ordering_fields = ('payment_date', '-payment_date')

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)


class PaymentCreateAPIView(APIView):
    """
    Создание платежа для курса через Stripe.
    POST /api/users/payments/create/  { "course_id": 1 }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course_id = serializer.validated_data['course_id']

        from lms.models import Course
        course = get_object_or_404(Course, id=course_id)

        # Сумма в копейках. Берём фиксированную цену или цену из курса, если добавите поле price
        amount_rub = 1000
        amount_kopecks = amount_rub * 100

        # 1. Продукт
        product = services.create_stripe_product(name=course.name)

        # 2. Цена
        price = services.create_stripe_price(product_id=product.id, amount=amount_kopecks)

        # 3. Сессия
        success_url = request.build_absolute_uri('/api/users/payments/success/')
        session = services.create_stripe_session(price_id=price.id, success_url=success_url)

        # 4. Сохраняем Payment
        payment = Payment.objects.create(
            user=request.user,
            payment_date=timezone.now(),
            course=course,
            amount=amount_rub,
            payment_method=Payment.TRANSFER,
            stripe_product_id=product.id,
            stripe_price_id=price.id,
            stripe_session_id=session.id,
            payment_link=session.url,
            status='pending',
        )

        return Response(
            {
                'payment_id': payment.id,
                'payment_link': payment.payment_link,
                'session_id': payment.stripe_session_id,
                'status': payment.status,
            },
            status=status.HTTP_201_CREATED,
        )


class PaymentStatusAPIView(APIView):
    """
    Проверка статуса платежа через Stripe Session Retrieve.
    GET /api/users/payments/<payment_id>/status/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        payment = get_object_or_404(Payment, id=pk, user=request.user)

        if not payment.stripe_session_id:
            return Response(
                {'error': 'У платежа нет Stripe-сессии.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session = services.retrieve_stripe_session(payment.stripe_session_id)

        payment.status = session.payment_status  # 'unpaid' / 'paid' / 'no_payment_required'
        payment.save(update_fields=['status'])

        return Response(
            {
                'payment_id': payment.id,
                'stripe_session_id': payment.stripe_session_id,
                'status': payment.status,
                'payment_link': payment.payment_link,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# HTML-регистрация и активация
# ============================================================

def register(request):
    """Простая регистрация пользователя (HTML)."""
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