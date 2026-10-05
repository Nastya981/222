from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Payment


class PublicUserSerializer(serializers.ModelSerializer):
    """Публичная информация о пользователе (для чужого профиля).
    Без пароля, фамилии, истории платежей."""

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'city', 'avatar')


class PrivateUserSerializer(serializers.ModelSerializer):
    """Полная информация о пользователе (для своего профиля)."""

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'phone', 'city', 'avatar')
        read_only_fields = ('id', 'email')


# Оставляем UserSerializer — совместимость с UserViewSet по умолчанию
class UserSerializer(serializers.ModelSerializer):
    """Для обновления профиля (без пароля)."""
    class Meta:
        model = User
        fields = ('id', 'email', 'phone', 'city', 'avatar')
        read_only_fields = ('id', 'email')


class UserCreateSerializer(serializers.ModelSerializer):
    """Для регистрации через API. Пароль хешируется."""

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )

    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'password_confirm', 'first_name', 'last_name', 'phone', 'city', 'avatar')
        read_only_fields = ('id',)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Пользователь с таким email уже существует.')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({'password_confirm': 'Пароли не совпадают.'})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ('id', 'payment_date', 'amount', 'payment_method', 'course', 'lesson')