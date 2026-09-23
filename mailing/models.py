from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Recipient(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recipients",
        verbose_name="Владелец",
    )
    email = models.EmailField(verbose_name="Email")
    full_name = models.CharField(max_length=200, verbose_name="Ф. И. О.")
    comment = models.TextField(blank=True, verbose_name="Комментарий")

    class Meta:
        verbose_name = "Получатель"
        verbose_name_plural = "Получатели"
        constraints = [
            models.UniqueConstraint(
                fields=("owner", "email"),
                name="unique_recipient_email_for_owner",
            )
        ]

    def __str__(self) -> str:
        return f"{self.full_name} ({self.email})"


class Message(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="Владелец",
    )
    subject = models.CharField(max_length=200, verbose_name="Тема письма")
    body = models.TextField(verbose_name="Тело письма")

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"

    def __str__(self) -> str:
        return self.subject


class Mailing(models.Model):
    CREATED = "created"
    STARTED = "started"
    COMPLETED = "completed"

    STATUS_CHOICES = [
        (CREATED, "Создана"),
        (STARTED, "Запущена"),
        (COMPLETED, "Завершена"),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mailings",
        verbose_name="Владелец",
    )
    start_time = models.DateTimeField(verbose_name="Дата и время начала")
    end_time = models.DateTimeField(verbose_name="Дата и время окончания")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=CREATED,
        verbose_name="Статус",
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        verbose_name="Сообщение",
    )
    recipients = models.ManyToManyField(Recipient, verbose_name="Получатели")

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"

    def __str__(self) -> str:
        return f"Рассылка №{self.pk}: {self.message.subject}"

    def clean(self) -> None:
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError("Дата начала должна быть раньше даты окончания.")

    def update_status(self) -> None:
        now = timezone.now()
        if now < self.start_time:
            new_status = self.CREATED
        elif now <= self.end_time:
            new_status = self.STARTED
        else:
            new_status = self.COMPLETED

        if self.status != new_status:
            self.status = new_status
            self.save(update_fields=("status",))


class Attempt(models.Model):
    SUCCESS = "success"
    FAILED = "failed"

    STATUS_CHOICES = [
        (SUCCESS, "Успешно"),
        (FAILED, "Не успешно"),
    ]

    attempt_time = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время попытки")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name="Статус")
    server_response = models.TextField(blank=True, verbose_name="Ответ сервера")
    mailing = models.ForeignKey(
        Mailing,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name="Рассылка",
    )

    class Meta:
        verbose_name = "Попытка рассылки"
        verbose_name_plural = "Попытки рассылок"

    def __str__(self) -> str:
        return f"Попытка {self.attempt_time}: {self.status}"