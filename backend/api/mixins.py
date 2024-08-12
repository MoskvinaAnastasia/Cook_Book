from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from api.serializers import RecipeResponseSerializer


class RecipeListMixin:
    model_class = None
    action_name = None

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def add_to_list(self, request, pk=None):
        """Добавить рецепт в список (корзина или избранное)."""
        recipe = self.get_object()
        user = request.user
        if self.model_class.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {'errors': f'Рецепт уже добавлен в {self.action_name}.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        self.model_class.objects.create(user=user, recipe=recipe)
        serializer = RecipeResponseSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @add_to_list.mapping.delete
    def remove_from_list(self, request, pk=None):
        """Удалить рецепт из списка (корзина или избранное)."""
        recipe = self.get_object()
        user = request.user
        if not self.model_class.objects.filter(user=user,
                                               recipe=recipe).exists():
            return Response(
                {'errors': f'Рецепт не был добавлен в {self.action_name}.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        self.model_class.objects.filter(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
