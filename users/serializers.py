from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Для чтения и обновления профиля (без пароля)."""

    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name',
            'phone', 'city', 'avatar', 'telegram_chat_id',
            'is_active', 'created_at',
        )
        read_only_fields = ('id', 'email', 'is_active', 'created_at')


class UserCreateSerializer(serializers.ModelSerializer):
    """Регистрация через API. Пароль хешируется."""

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
        fields = (
            'id', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone', 'city',
            'avatar', 'telegram_chat_id',
        )
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