from django.contrib.auth import get_user_model
from django.db.models import BooleanField, Exists, OuterRef, Value
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from djoser.views import UserViewSet as DjoserUserViewSet

from api.filters import IngredientFilter, RecipeFilter
from api.mixins import RecipeListMixin
from api.pagination import LimitPagePagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (AvatarUserSerializer, IngredientSerializer,
                             RecipeCreateSerializer, RecipeGetSerializer,
                             ShortLinkSerializer, SubscriptionSerializer,
                             TagSerializer)
from api.shopping_cart import get_shopping_list
from recipes.models import (FavoriteRecipe, Ingredient, Recipe,
                            ShortLink, ShoppingCart, Tag)
from users.models import Follower

User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    """
    Вьюсет для работы с пользователями.
    """

    queryset = User.objects.all()
    pagination_class = LimitPagePagination

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return (AllowAny(),)
        return super().get_permissions()

    @action(detail=False, methods=['put'], url_path='me/avatar',
            permission_classes=[IsAuthenticated])
    def avatar(self, request, *args, **kwargs):
        """
        Добавление или обновление аватара текущего пользователя.
        """
        user = request.user
        serializer = AvatarUserSerializer(user, data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

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
    def subscribe(self, request, id=None):
        """Подписка на пользователей."""
        user = request.user
        author = get_object_or_404(User, pk=id)

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
    recipe = get_object_or_404(Recipe, id=recipe_id)
    short_link, created = ShortLink.objects.get_or_create(recipe=recipe)
    serializer = ShortLinkSerializer(short_link)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def redirect_short_link(request, short_link):
    """Перенаправляет на соответствующий рецепт по короткой ссылке."""
    short_link_obj = get_object_or_404(ShortLink, short_link=short_link)
    return redirect(reverse('recipes-detail', args=[short_link_obj.recipe.pk]))


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

        if self.request.user.is_authenticated:
            favorite_subquery = FavoriteRecipe.objects.filter(
                user=self.request.user,
                recipe=OuterRef('pk')
            )
            shopping_cart_subquery = ShoppingCart.objects.filter(
                user=self.request.user,
                recipe=OuterRef('pk')
            )
            queryset = queryset.annotate(
                is_favorited=Exists(favorite_subquery),
                is_in_shopping_cart=Exists(shopping_cart_subquery)
            )
        else:
            queryset = queryset.annotate(
                is_favorited=Value(False, output_field=BooleanField()),
                is_in_shopping_cart=Value(False, output_field=BooleanField())
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

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """Добавить рецепт в избранное текущего пользователя."""
        self.model_class = FavoriteRecipe
        self.action_name = 'избранное'
        return self.add_to_list(request, pk)

    @favorite.mapping.delete
    def remove_favorite(self, request, pk=None):
        """Удалить рецепт из избранного текущего пользователя."""
        self.model_class = FavoriteRecipe
        self.action_name = 'избранное'
        return self.remove_from_list(request, pk)

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        """Добавить рецепт в корзину текущего пользователя."""
        self.model_class = ShoppingCart
        self.action_name = 'корзина'
        return self.add_to_list(request, pk)

    @shopping_cart.mapping.delete
    def remove_shopping_cart(self, request, pk=None):
        """Удалить рецепт из корзины текущего пользователя."""
        self.model_class = ShoppingCart
        self.action_name = 'корзина'
        return self.remove_from_list(request, pk)

    @action(detail=True, methods=['get'],
            permission_classes=[AllowAny])
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
