from django.contrib.auth.validators import UnicodeUsernameValidator
from djoser.serializers import UserSerializer, UserCreateSerializer
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from rest_framework import serializers
from recipes.models import (Ingredient, Tag,)

User = get_user_model()


class CustomUserSerializer(UserSerializer):
    """Сериализатор для получения информации о пользователе."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar')
        
    def get_is_subscribed(self, obj):
        pass

    def get_avatar(self, obj):
        pass


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для регистрация пользователей."""

    email = serializers.EmailField(required=True)
    username = serializers.CharField(
        required=True,
        validators=[UnicodeUsernameValidator()],
        max_length=150
    )
    first_name = serializers.CharField(required=True,
                                       max_length=150)
    last_name = serializers.CharField(required=True,
                                      max_length=150)
    password = serializers.CharField(write_only=True,
                                     required=True)

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password')


class TokenCreateSerializer(serializers.Serializer):
    """Сериализатор для получения токена."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError('Неверные учетные данные.')

        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    """Сериализатор для изменения пароля."""

    current_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        current_password = attrs.get('current_password')
        user = self.context['request'].user

        if not user.check_password(current_password):
            raise serializers.ValidationError(
                {"current_password": "Неправильный текущий пароль."})

        return attrs


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""
    
    slug = serializers.SlugField(
        validators=[UnicodeUsernameValidator()]
    )

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')
