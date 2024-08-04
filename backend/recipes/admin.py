from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import (Ingredient, FavoriteRecipe, Recipe,
                     RecipeIngredient, ShoppingCart, Tag)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'image_tag')
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('tags',)

    def image_tag(self, obj):
        if obj.image:
            return mark_safe('<img src="{}" width="150" height="100" />'.format(obj.image.url))
        return None
    
    image_tag.short_description = 'Фото рецепта'

@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    ordering = ('name',)
