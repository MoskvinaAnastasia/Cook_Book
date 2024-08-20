from django.contrib.auth.models import AbstractUser
from django.db import models

from .constants import MAX_LENGTH_USER_CHARFIELD, MAX_LENGTH_USER_EMAIL


class User(AbstractUser):
    """Класс кастомных пользователей."""

    first_name = models.CharField(
        max_length=MAX_LENGTH_USER_CHARFIELD,
        verbose_name='Имя',
        help_text='Обязательное поле',
        blank=False,
        null=False,
    )
    last_name = models.CharField(
        max_length=MAX_LENGTH_USER_CHARFIELD,
        verbose_name='Фамилия',
        help_text='Обязательное поле',
        blank=False,
        null=False,
    )
    username = models.CharField(
        max_length=MAX_LENGTH_USER_CHARFIELD,
        verbose_name='Имя пользователя',
        help_text='Обязательное поле',
        unique=True,
        blank=False,
        null=False,
    )
    email = models.EmailField(
        max_length=MAX_LENGTH_USER_EMAIL,
        verbose_name='Адрес Электронной почты',
        help_text='Обязательное поле',
        unique=True,
        blank=False,
        null=False,
    )
    password = models.CharField(
        max_length=128,
        verbose_name='Пароль',
        help_text='Обязательное поле',
        blank=False,
        null=False,
    )
    avatar = models.ImageField(
        upload_to='users/', null=True, default=None,
        verbose_name='Аватар',
    )

    def __str__(self):
        return self.username


class Follower(models.Model):
    """Класс для подписки на автора."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
        help_text='Пользователь, который подписывается',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
        help_text='Автор, на которого подписываются',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='user_author_unique'
            ),
        )

    def __str__(self):
        return f'{self.user.username} подписан на {self.author.username}'
