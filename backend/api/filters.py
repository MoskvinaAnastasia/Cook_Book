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
        request = self.request
        if not request.user.is_authenticated:
            return queryset.none()
        if value:
            return queryset.filter(favorite__user=request.user)
        return queryset.exclude(favorite__user=request.user)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        request = self.request
        if not request.user.is_authenticated:
            return queryset.none()
        if value:
            return queryset.filter(shopping_cart__user=request.user)
        return queryset.exclude(shopping_cart__user=request.user)