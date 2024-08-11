import random
import string

from django.db import models

from users.models import User
from .constants import MAX_LENGTH_NAME_CHARFIELD, MAX_LENGTH_TAG


class Ingredient(models.Model):
    """Класс ингредиенты."""

    name = models.CharField(
        max_length=MAX_LENGTH_NAME_CHARFIELD,
        verbose_name='Название',
        help_text='Обязательное поле',
        blank=False,
        null=False,
    )

    measurement_unit = models.CharField(
        max_length=MAX_LENGTH_NAME_CHARFIELD,
        verbose_name='Единица измерения',
        help_text='Обязательное поле',
        blank=False,
        null=False,
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name} - {self.measurement_unit}'


class Tag(models.Model):
    """Класс Тег для группировки рецептов по тегам."""

    name = models.CharField(
        max_length=MAX_LENGTH_TAG,
        verbose_name='Название',
        help_text='Обязательное поле',
        unique=True,
        blank=False,
        null=False,
    )

    slug = models.SlugField(
        max_length=MAX_LENGTH_TAG,
        verbose_name='Слаг',
        help_text='Обязательное поле',
        unique=True,
        blank=False,
        null=False,
    )

    class Meta:
        verbose_name = 'Тег',
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Класс Рецепт."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта',
        help_text='Обязательное поле',
    )

    name = models.CharField(
        max_length=MAX_LENGTH_NAME_CHARFIELD,
        verbose_name='Название',
        help_text='Обязательное поле',
        blank=False,
        null=False,
    )

    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='Картинка',
        help_text='Обязательное поле',
        blank=False,
        null=False,
    )

    text = models.TextField(
        max_length=700,
        verbose_name='Текстовое описание',
        blank=False,
        null=False,
    )

    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
        help_text='Обязательное поле',
        blank=False,
    )

    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        help_text='Обязательное поле',
        blank=False,
    )

    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления в минутах',
        help_text='Обязательное поле',
        default=0,
        blank=False,
        null=False,
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f"Рецепт: {self.name}. Автор: {self.author.username}"


class FavoriteRecipe(models.Model):
    """
    Класс избранных рецептов пользователя.
    Модель связывает Recipe и User.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_recipes',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='users_recipes',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'

    def __str__(self):
        return f'{self.user.username} добавил {self.recipe.name} в избраннное'


class ShoppingCart(models.Model):
    """
    Класс корзины пользователя, куда он положил нужный рецепт.
    Модель связывает User и Recipe.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_carts',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        return (f'{self.user.username} добавил'
                f'{self.recipe.name} в список покупок')


class RecipeIngredient(models.Model):
    """Класс для связи модели Recipe и модели Ingredient."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_amounts',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='used_in_recipes',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        blank=False,
        null=False,
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Количество ингредиентов в рецепте'

    def __str__(self):
        return f'{self.recipe.name} - {self.ingredient.name} ({self.amount})'


class ShortLink(models.Model):
    """Модель для хранения коротких ссылок на рецепты."""

    recipe = models.OneToOneField(Recipe, on_delete=models.CASCADE,
                                  related_name='short_link')
    short_link = models.CharField(max_length=3, unique=True,
                                  blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.short_link:
            self.short_link = self.generate_short_link()
        super().save(*args, **kwargs)

    def generate_short_link(self):
        """Генерирует уникальную короткую ссылку."""
        length = 3
        characters = string.ascii_letters + string.digits
        while True:
            short_link = ''.join(random.choices(characters, k=length))
            if not ShortLink.objects.filter(short_link=short_link).exists():
                break
        return short_link
