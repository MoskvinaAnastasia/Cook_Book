from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Класс кастомных пользователей."""

    first_name = models.CharField(
        max_length=128,
        verbose_name='Имя',
        help_text='Обязательное поле',
        blank=False,
        null=False,
    )
    last_name = models.CharField(
        max_length=128,
        verbose_name='Фамилия',
        help_text='Обязательное поле',
        blank=False,
        null=False,
    )
    username = models.CharField(
        max_length=128,
        verbose_name='Имя пользователя',
        help_text='Обязательное поле',
        unique=True,
        blank=False,
        null=False,
    )
    email = models.EmailField(
        max_length=100,
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

    def __str__(self):
        return self.username
