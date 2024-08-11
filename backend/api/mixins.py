from rest_framework.response import Response
from rest_framework import status


class RecipeActionMixin:
    """
    Миксин для обработки добавления и удаления рецептов.
    в/из списка покупок и избранного.
    """

    def get_recipe(self, request, pk=None):
        """Получить рецепт по первичному ключу."""
        return self.get_object()

    def get_user(self, request):
        """Получить текущего пользователя."""
        return request.user

    def add_to_list(self, model, user, recipe):
        """Добавить рецепт в список (покупок или избранное)."""
        if model.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {'errors': 'Рецепт уже добавлен.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        model.objects.create(user=user, recipe=recipe)
        return None

    def remove_from_list(self, model, user, recipe):
        """Удалить рецепт из списка (покупок или избранное)."""
        if not model.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {'errors': 'Рецепт не был добавлен.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        model.objects.filter(user=user, recipe=recipe).delete()
        return None
