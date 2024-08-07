from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Follower, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'username', 'first_name',
                    'last_name', 'avatar_tag')
    list_filter = ('email', 'username',)
    search_fields = ('email', 'username', 'first_name', 'last_name',)

    def avatar_tag(self, obj):
        if obj.avatar:
            return mark_safe('<img src="{}" width="150"'
                             'height="150" />'.format(obj.avatar.url))

    avatar_tag.short_description = 'Аватар'


@admin.register(Follower)
class FollowerAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author',)
    list_filter = ('user', 'author',)
    search_fields = ('user', 'author',)
