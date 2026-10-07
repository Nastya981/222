from django.conf import settings
from django.db import models


class Habit(models.Model):
    """Модель полезной/приятной привычки."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='habits',
        verbose_name='Пользователь',
    )
    place = models.CharField(max_length=255, verbose_name='Место')
    time = models.TimeField(verbose_name='Время выполнения')
    action = models.CharField(max_length=255, verbose_name='Действие')
    is_pleasant = models.BooleanField(
        default=False,
        verbose_name='Приятная привычка',
    )
    related_habit = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_to',
        verbose_name='Связанная привычка',
    )
    periodicity = models.PositiveSmallIntegerField(
        default=1,
        verbose_name='Периодичность (дней)',
    )
    reward = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Вознаграждение',
    )
    duration = models.PositiveSmallIntegerField(
        verbose_name='Время на выполнение (сек)',
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name='Публичная',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Привычка'
        verbose_name_plural = 'Привычки'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.action} в {self.time} ({self.user})'