from djoser.views import UserViewSet
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from api.serializers import (CustomUserCreateSerializer, CustomUserSerializer,
                             IngredientSerializer, TagSerializer,)
from api.pagination import LimitPagePagination
from recipes.models import (Ingredient, Tag,)


class CustomUserViewSet(UserViewSet):
    """Вьюсет для регистрации пользователя."""

    serializer_class = CustomUserCreateSerializer


class CustomUserProfileViewSet(UserViewSet):
    """Вьюсет для получения информации о пользователе."""

    serializer_class = CustomUserSerializer
    lookup_field = 'id'


class UserListViewSet(UserViewSet):
    """Вьюсет для получения списка пользователей с пагинацией."""

    serializer_class = CustomUserSerializer
    pagination_class = LimitPagePagination
    permission_classes = (AllowAny, )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Получение списков тегов и информации о теге по id.
    Создание и редактирование тегов доступно только в админ-панеле.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny, )
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Получение списка ингредиентов, информации об ингредиенте по id.
    Создание и редактирование ингредиентов доступно только в админ-панеле.
    Доступен поиск по частичному вхождению в начале названия ингредиента.
    """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
