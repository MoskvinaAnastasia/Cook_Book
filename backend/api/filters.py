from django_filters.rest_framework import filters, FilterSet

from recipes.models import Ingredient, Recipe, Tag

class IngredientFilter(FilterSet):
    """Фильтрация ингредиентов."""

    name = filters.CharFilter(lookup_expr='istartswith',)

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    """Фильтр рецептов."""

    tags = filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug',
    )
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        """Фильтрует рецепты по тому, находятся ли они в избранном у текущего пользователя."""
        request = self.request
        if not request.user.is_authenticated:
            return queryset.none()
        if value:
            return queryset.filter(favorite_recipes__user=request.user)
        return queryset.exclude(favorite_recipes__user=request.user)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтрует рецепты по тому, находятся ли они в списке покупок у текущего пользователя."""
        request = self.request
        if not request.user.is_authenticated:
            return queryset.none()
        if value:
            return queryset.filter(in_shopping_carts__user=request.user)
        return queryset.exclude(in_shopping_carts__user=request.user)