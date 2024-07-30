from djoser.views import UserViewSet
from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from api.serializers import (CustomUserCreateSerializer, CustomUserSerializer,
                             IngredientSerializer, TagSerializer,)
from api.pagination import LimitPagePagination
from recipes.models import (Ingredient, Tag,)

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    """
    Вьюсет для работы с пользователями.
    Обрабатываемые эндпоинты:
    - GET /users/: Список всех пользователей (с пагинацией).
    - POST /users/: Создание нового пользователя.
    - GET /users/{id}/: Получение профиля пользователя по ID.
    - GET /users/me/: Получение профиля текущего пользователя.
    """

    queryset = User.objects.all()
    pagination_class = LimitPagePagination

    def get_permissions(self):
        if self.action in ['create', 'retrieve', 'list',]:
            self.permission_classes = [AllowAny]
        else:
            self.permission_classes = [IsAuthenticatedOrReadOnly]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        elif self.action == 'me' or self.action == 'retrieve':
            return CustomUserSerializer
        elif self.action == 'list':
            return CustomUserSerializer
        return super().get_serializer_class()


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
