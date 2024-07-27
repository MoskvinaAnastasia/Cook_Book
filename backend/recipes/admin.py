from django.contrib import admin

from .models import (Ingredient, FavoriteRecipe, Recipe,
                     RecipeIngredient, ShoppingCart, Tag)


admin.site.register(Ingredient)
admin.site.register(FavoriteRecipe)
admin.site.register(Recipe)
admin.site.register(RecipeIngredient)
admin.site.register(ShoppingCart)
admin.site.register(Tag)
