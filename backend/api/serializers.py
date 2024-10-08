from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import transaction
from djoser.serializers import \
    UserCreateSerializer as DjoserUserCreateSerializer
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import Ingredient, Recipe, RecipeIngredient, ShortLink, Tag
from rest_framework import serializers
from users.constants import MAX_LENGTH_USER_CHARFIELD
from users.models import Follower

User = get_user_model()


class UserSerializer(DjoserUserSerializer):
    """Сериализатор для получения информации о пользователе."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на данного автора."""
        user = self.context['request'].user
        if user.is_authenticated:
            return Follower.objects.filter(user=user, author=obj).exists()
        return False

    def get_avatar(self, obj):
        """Возвращает URL аватара пользователя или None, если аватара нет."""
        if obj.avatar:
            return obj.avatar.url
        return None


class UserCreateSerializer(DjoserUserCreateSerializer):
    """Сериализатор для регистрация пользователей."""

    email = serializers.EmailField(required=True)
    username = serializers.CharField(
        required=True,
        validators=[UnicodeUsernameValidator()],
        max_length=MAX_LENGTH_USER_CHARFIELD
    )
    first_name = serializers.CharField(
        required=True,
        max_length=150)
    last_name = serializers.CharField(
        required=True,
        max_length=150)
    password = serializers.CharField(
        write_only=True,
        required=True)

    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name', 'password')


class AvatarUserSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления/удаления аватара."""

    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def validate_avatar(self, value):
        """Проверяет, что поле avatar передано."""
        if not value:
            raise serializers.ValidationError('Поле avatar обязательно.')
        return value


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


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для получения ингредиентов в рецепте."""

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeGetSerializer(serializers.ModelSerializer):
    """Сериализатор для получения рецепта."""

    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, required=True)
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='ingredient_amounts',
        required=True
    )
    is_favorited = serializers.BooleanField(default=False)
    is_in_shopping_cart = serializers.BooleanField(default=False)
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )
        read_only_fields = ('author', 'tags', 'ingredients')


class IngredientCreateSerializer(serializers.ModelSerializer):
    """Серилизатор для Проверки ингредиента при создании рецепта."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField(write_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')

    def validate_amount(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Количество должно быть больше или равно 1'
            )
        return value


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Серилизатор для Создания и обновления рецептов."""

    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        required=True
    )
    ingredients = IngredientCreateSerializer(
        write_only=True,
        many=True,
        required=True
    )
    image = Base64ImageField(required=True)
    name = serializers.CharField(max_length=256)
    text = serializers.CharField()
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'ingredients', 'image',
                  'name', 'text', 'cooking_time')

    def validate_cooking_time(self, value):

        if value == 0:
            raise serializers.ValidationError(
                'Время приготовления должно быть больше 0'
            )
        return value

    def validate_image(self, value):
        """Проверяет, что изображение предоставлено."""
        if value is None:
            raise serializers.ValidationError('Поле image обязательно.')
        return value

    def validate(self, data):
        """
        Проверяет, что ингредиенты и теги уникальны и существуют.
        и что они не пустые.
        """

        ingredients = data.get('ingredients', [])

        if not ingredients:
            raise serializers.ValidationError('Поле ingredients обязательно.')

        ingredienеts_list = [ingredient['id'] for ingredient in ingredients]
        if len(ingredienеts_list) != len(set(ingredienеts_list)):
            raise serializers.ValidationError(
                'Ингредиенты должны быть уникальными.')

        non_existing_ingredients = [
            ingredient_id for ingredient_id in ingredienеts_list
            if not Ingredient.objects.filter(id=ingredient_id).exists()
        ]
        if non_existing_ingredients:
            raise serializers.ValidationError(
                f"Ингредиент с id {non_existing_ingredients} не существует."
            )

        tags = data.get('tags', [])
        if not tags:
            raise serializers.ValidationError('Поле tags обязательно.')
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError('Теги должны быть уникальными.')

        return data

    @transaction.atomic
    def create(self, validated_data):
        """Создает новый рецепт."""
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        ingredient_ids = [ingredient_data.get('id')
                          for ingredient_data in ingredients_data]
        ingredients = Ingredient.objects.filter(id__in=ingredient_ids)
        ingredient_dict = {
            ingredient.id: ingredient for ingredient in ingredients}

        recipe_ingredients = []
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data.get('id')
            amount = ingredient_data.get('amount')
            ingredient = ingredient_dict.get(ingredient_id)
            if ingredient:
                recipe_ingredients.append(
                    RecipeIngredient(
                        recipe=recipe,
                        ingredient=ingredient,
                        amount=amount
                    )
                )
        RecipeIngredient.objects.bulk_create(recipe_ingredients)
        return recipe

    def create_ingredients(self, ingredients, recipe):
        """Создает и связывает ингредиенты с рецептом."""

        ingredient_ids = [ingredient['id'] for ingredient in ingredients]
        ingredient_instances = Ingredient.objects.filter(id__in=ingredient_ids)
        ingredient_dict = {
            ingredient.id: ingredient for ingredient in ingredient_instances}
        ingredients_list = [
            RecipeIngredient(
                recipe=recipe,
                amount=ingredient['amount'],
                ingredient=ingredient_dict[ingredient['id']]
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(ingredients_list)

    @transaction.atomic
    def update(self, instance, validated_data):
        """Обновляет существующий рецепт."""
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)

        if ingredients is None:
            raise serializers.ValidationError(
                'Поле "ingredients" обязательно для обновления рецепта.')
        instance = super().update(instance, validated_data)

        if tags is not None:
            instance.tags.set(tags)
        if ingredients is not None:
            instance.ingredients.clear()
            self.create_ingredients(ingredients, instance)
        instance.save()

        return instance

    def to_representation(self, instance):
        """Используем RecipeGetSerializer для формирования ответа."""
        return RecipeGetSerializer(instance, context=self.context).data


class RecipeResponseSerializer(serializers.ModelSerializer):
    """
    Сериализатор для ответа при добавлении рецепта.
    в список покупок или избранное.
    """

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(UserSerializer):
    """Получение подписок пользователя."""

    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count', 'avatar')

    def get_recipes(self, object):
        request = self.context['request']
        limit = request.GET.get('recipes_limit')
        recipes = Recipe.objects.filter(author=object)
        if limit:
            recipes = recipes[:int(limit)]
        serializer = RecipeResponseSerializer(recipes, many=True)
        return serializer.data

    def get_recipes_count(self, object):
        return object.recipes.count()

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Follower.objects.filter(user=user, author=obj).exists()


class ShortLinkSerializer(serializers.ModelSerializer):
    """Сериализатор для короткой ссылки."""
    short_link = serializers.SerializerMethodField()

    class Meta:
        model = ShortLink
        fields = ('short_link',)

    def get_short_link(self, obj):
        """Создает полный URL для короткой ссылки."""
        base_url = f'{settings.SITE_HOSTNAME}/s/'
        return f"{base_url}{obj.short_link}"

    def to_representation(self, instance):
        """Преобразует ключи в формат с дефисом."""
        representation = super().to_representation(instance)
        return {
            'short-link': representation['short_link']
        }
