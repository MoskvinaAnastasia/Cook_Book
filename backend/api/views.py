from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.views import APIView

from djoser.serializers import SetPasswordSerializer

from api.pagination import LimitPagePagination
from api.permissions import IsAuthorAdminAuthenticated
from recipes.models import (Ingredient, Recipe, Tag)
from api.serializers import (AvatarUserSerializer, CustomUserCreateSerializer,
                             CustomUserSerializer, IngredientSerializer,
                             TagSerializer, TokenCreateSerializer)


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
            serializer = AvatarUserSerializer(user, data=request.data,
                                              partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete()
                user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)


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


class RecipeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Вьюсет для Создание и получение рецептов.
    """

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorAdminAuthenticated, )
    pagination_class = LimitPagePagination
    