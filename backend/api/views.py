from rest_framework import viewsets
from api.serializers import (TagSerializer,)
from recipes.models import(Tag,)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Получение списков тегов и информации о теге по id.
    Создание и редактирование тегов доступно только в админ-панеле.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
