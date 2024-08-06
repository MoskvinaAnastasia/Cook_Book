from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import status
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.views import APIView

from djoser.serializers import SetPasswordSerializer

from .filters import IngredientFilter, RecipeFilter
from api.pagination import LimitPagePagination
from api.permissions import IsAuthorAdminAuthenticated
from recipes.models import (FavoriteRecipe, Ingredient, Recipe, 
                            ShortLink, ShoppingCart, Tag)
from api.serializers import (AvatarUserSerializer, CustomUserCreateSerializer,
                             CustomUserSerializer, IngredientSerializer,
                             RecipeCreateSerializer, RecipeGetSerializer,
                             RecipeResponseSerializer, ShortLinkSerializer,
                             SubscriptionSerializer,
                             TagSerializer, TokenCreateSerializer,
                             )
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
    serializer_class = CustomUserSerializer

    def get_permissions(self):
        if self.action in ('create', 'retrieve', 'list'):
            self.permission_classes = (AllowAny, )
        else:
            self.permission_classes = (IsAuthenticatedOrReadOnly, )
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        elif self.action == 'retrieve':
            return CustomUserSerializer
        elif self.action == 'list':
            return CustomUserSerializer
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
    
    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar',
            permission_classes=[IsAuthenticated])
    def avatar(self, request, *args, **kwargs):
        """
        Добавления/обновления и удаления аватара текущего пользователя.
        """
        user = request.user

        if request.method == 'PUT':
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

        elif request.method == 'DELETE':
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
    
    @action(methods=['post', 'delete'], detail=True, permission_classes=[IsAuthenticated])
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
            serializer = SubscriptionSerializer(author, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        if request.method == 'DELETE':
            if instance.exists():
                instance.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response('Вы не подписаны на автора', status=status.HTTP_400_BAD_REQUEST)

class TokenCreateView(APIView):
    """
    Вьюсет для получения токена авторизации.
    """
    permission_classes = (AllowAny, )
    serializer_class = TokenCreateSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = authenticate(email=email, password=password)

            if user:
                token, created = Token.objects.get_or_create(user=user)
                return Response({'auth_token': token.key},
                                status=status.HTTP_201_CREATED)
            return Response({'detail': 'Неверные учетные данные.'},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
        return Response({'detail': 'Рецепт не найден.'}, status=status.HTTP_404_NOT_FOUND)
    
    short_link, created = ShortLink.objects.get_or_create(recipe=recipe)
    
    serializer = ShortLinkSerializer(short_link)
    return Response(serializer.data, status=status.HTTP_200_OK)


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Вьюсет для Создание и получение рецептов.
    """

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorAdminAuthenticated, )
    pagination_class = LimitPagePagination
    filterset_class = RecipeFilter
    
    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeGetSerializer
        return RecipeCreateSerializer
        
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    
    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        """
        Добавить или удалить рецепт из списка покупок текущего пользователя.
        Использует метод запроса для определения действия:
        - POST: добавить рецепт в список покупок
        - DELETE: удалить рецепт из списка покупок
        """
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже добавлен в список покупок.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = RecipeResponseSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            if not ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт не был добавлен в список покупок.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.filter(user=user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        
    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """
        Добавить или удалить рецепт из избранного текущего пользователя.
        Использует метод запроса для определения действия:
        - POST: добавить рецепт в избранное
        - DELETE: удалить рецепт из избранного
        """
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            if FavoriteRecipe.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже добавлен в избранное.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            FavoriteRecipe.objects.create(user=user, recipe=recipe)
            serializer = RecipeResponseSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            if not FavoriteRecipe.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт не был добавлен в избранное.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            FavoriteRecipe.objects.filter(user=user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def get_link(self, request, pk=None):
        """Получить короткую ссылку на рецепт."""
        recipe = self.get_object()
        short_link, created = ShortLink.objects.get_or_create(recipe=recipe)
        serializer = ShortLinkSerializer(short_link)
        return Response(serializer.data, status=status.HTTP_200_OK)
