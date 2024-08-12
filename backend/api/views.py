from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef, Value, BooleanField
from django.db.models.functions import Coalesce
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAdminUser, IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from djoser.serializers import SetPasswordSerializer

from api.filters import IngredientFilter, RecipeFilter
from .mixins import RecipeListMixin
from api.pagination import LimitPagePagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (AvatarUserSerializer, UserCreateSerializer,
                             UserSerializer, IngredientSerializer,
                             RecipeCreateSerializer, RecipeGetSerializer,
                             ShortLinkSerializer,
                             SubscriptionSerializer, TagSerializer,)
from api.shopping_cart import get_shopping_list
from recipes.models import (FavoriteRecipe, Ingredient, Recipe,
                            ShortLink, ShoppingCart, Tag)
from users.models import Follower

User = get_user_model()


class CustomUserViewSet(viewsets.ModelViewSet):
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
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ('create', 'retrieve', 'list'):
            self.permission_classes = (AllowAny, )
        elif self.action in ('update', 'partial_update', 'destroy'):
            self.permission_classes = (IsAuthorOrReadOnly, IsAdminUser)
        else:
            self.permission_classes = (IsAuthenticatedOrReadOnly, )
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['retrieve', 'list']:
            return UserSerializer
        return super().get_serializer_class()

    @action(methods=['get'], detail=False,
            permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        """
        Получение информации о текущем аутентифицированном пользователе.
        """
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(methods=['post'], detail=False,
            permission_classes=[IsAuthenticated])
    def set_password(self, request, *args, **kwargs):
        """
        Изменение пароля текущего пользователя.
        """
        serializer = SetPasswordSerializer(data=request.data,
                                           context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['put'], url_path='me/avatar',
            permission_classes=[IsAuthenticated])
    def avatar(self, request, *args, **kwargs):
        """
        Добавление или обновление аватара текущего пользователя.
        """
        user = request.user
        serializer = AvatarUserSerializer(user, data=request.data)

        if not request.data.get('avatar'):
            return Response(
                {'detail': 'Поле avatar обязательно.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @avatar.mapping.delete
    def delete_avatar(self, request, *args, **kwargs):
        """
        Удаление аватара текущего пользователя.
        """
        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': 'Аватар отсутствует.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False)
    def subscriptions(self, request):
        """Просмотр подписок пользователя."""
        user = self.request.user
        subscriptions = User.objects.filter(following__user=user)
        list = self.paginate_queryset(subscriptions)
        serializer = SubscriptionSerializer(
            list, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(methods=['post', 'delete'], detail=True,
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        """Подписка на пользователей."""
        user = self.request.user
        author = get_object_or_404(User, pk=pk)

        if user.id == author.id:
            return Response(
                {'detail': 'Нельзя подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        instance = Follower.objects.filter(author=author, user=user)
        if request.method == 'POST':
            if instance.exists():
                return Response('Вы уже подписаны',
                                status=status.HTTP_400_BAD_REQUEST)
            Follower.objects.create(user=user, author=author)
            serializer = SubscriptionSerializer(author,
                                                context={'request': request})
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if instance.exists():
                instance.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response('Вы не подписаны на автора',
                            status=status.HTTP_400_BAD_REQUEST)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Вьюсет для получение списков тегов и информации о теге по id.
    Создание и редактирование тегов доступно только в админ-панеле.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny, )
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Вьюсет для получение списка ингредиентов, информации об ингредиенте по id.
    Создание и редактирование ингредиентов доступно только в админ-панеле.
    Доступен поиск по частичному вхождению в начале названия ингредиента.
    """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


@api_view(['GET'])
def get_short_link(request, recipe_id):
    """
    Получение или создание короткой ссылки для рецепта.
    """
    try:
        recipe = Recipe.objects.get(id=recipe_id)
    except Recipe.DoesNotExist:
        return Response({'detail': 'Рецепт не найден.'},
                        status=status.HTTP_404_NOT_FOUND)

    short_link, created = ShortLink.objects.get_or_create(recipe=recipe)

    serializer = ShortLinkSerializer(short_link)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def redirect_short_link(request, short_link):
    """Перенаправляет на соответствующий рецепт по короткой ссылке."""
    short_link_obj = get_object_or_404(ShortLink, short_link=short_link)
    return redirect('recipes-detail', pk=short_link_obj.recipe.id)


class RecipeViewSet(RecipeListMixin, viewsets.ModelViewSet):
    """
    Вьюсет для Создание и получение рецептов.
    """

    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = LimitPagePagination
    filterset_class = RecipeFilter
    filter_backends = (DjangoFilterBackend,)
    ordering = ('-pub_date',)

    def get_queryset(self):
        queryset = Recipe.objects.all()
        user = (self.request.user if self.request.user.is_authenticated
                else None)
        favorite_subquery = FavoriteRecipe.objects.filter(
            user=user if user else Value(None),
            recipe=OuterRef('pk')
        )
        shopping_cart_subquery = ShoppingCart.objects.filter(
            user=user if user else Value(None),
            recipe=OuterRef('pk')
        )
        queryset = queryset.annotate(
            is_favorited=Coalesce(Exists(favorite_subquery), False),
            is_in_shopping_cart=Coalesce(Exists(shopping_cart_subquery), False)
        )
        return queryset

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeGetSerializer
        return RecipeCreateSerializer

    def get_serializer_context(self):
        return {'request': self.request}

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """Добавить рецепт в избранное текущего пользователя."""
        self.model_class = FavoriteRecipe
        self.action_name = 'избранное'
        return self.add_to_list(request, pk)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        """Удалить рецепт из избранного текущего пользователя."""
        self.model_class = FavoriteRecipe
        self.action_name = 'избранное'
        return self.remove_from_list(request, pk)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        """Добавить рецепт в список покупок текущего пользователя."""
        self.model_class = ShoppingCart
        self.action_name = 'список покупок'
        return self.add_to_list(request, pk)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        """Удалить рецепт из списка покупок текущего пользователя."""
        self.model_class = ShoppingCart
        self.action_name = 'список покупок'
        return self.remove_from_list(request, pk)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def get_link(self, request, pk=None):
        """Получить короткую ссылку на рецепт."""
        recipe = self.get_object()
        short_link, created = ShortLink.objects.get_or_create(recipe=recipe)
        serializer = ShortLinkSerializer(short_link)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """
        Скачивание списка покупок для авторизованного
        пользователя в формате TXT.
        """
        user = request.user

        try:
            file_buffer = get_shopping_list(user)
        except ValueError:
            return Response(
                {'detail': 'Ваш список покупок пуст.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return FileResponse(file_buffer,
                            as_attachment=True,
                            filename='shopping_cart.txt')
