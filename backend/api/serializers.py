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


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')
