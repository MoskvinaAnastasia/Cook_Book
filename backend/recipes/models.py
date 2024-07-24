from django.db import models


class Ingredient(models.Model):
    """Класс ингредиенты."""

    name = models.CharField(
        max_length=128,
        verbose_name='Название',
        help_text='Обязательное поле',
        blank=False,
        null=False,
    )

    measurement_unit = models.CharField(
        max_length=128,
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
        max_length=128,
        verbose_name='Название',
        help_text='Обязательное поле',
        unique=True,
        blank=False,
        null=False,
    )

    slug = models.SlugField(
        max_length=128,
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

    author = models.CharField(
        max_length=128,
        verbose_name='Автор рецепта',
        help_text='Обязательное поле',
    )

    name = models.CharField(
        max_length=128,
        verbose_name='Название',
        help_text='Обязательное поле',
        blank=False,
        null=False,
    )

    image = models.ImageField(
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