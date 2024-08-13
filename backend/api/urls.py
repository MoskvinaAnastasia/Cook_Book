from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (IngredientViewSet, TagViewSet,
                    UserViewSet, RecipeViewSet,
                    get_short_link)

router_v1 = DefaultRouter()

router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')
router_v1.register('users', UserViewSet, basename='user')
router_v1.register('recipes', RecipeViewSet, basename='recipes')


urlpatterns = [
    path('', include(router_v1.urls)),
    path('recipes/<int:recipe_id>/get-link/', get_short_link, name='get-link'),
    path('auth/', include('djoser.urls.authtoken')),
]
