from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils import timezone

from mailing.models import Attempt, Mailing


def send_mailing(mailing: Mailing) -> tuple[int, int]:
    now = timezone.now()
    if not mailing.start_time <= now <= mailing.end_time:
        raise ValidationError("Текущее время не входит в диапазон рассылки.")

    attempts: list[Attempt] = []
    success_count = 0
    fail_count = 0

    for recipient in mailing.recipients.all():
        try:
            sent = send_mail(
                subject=mailing.message.subject,
                message=mailing.message.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=False,
            )
            attempts.append(
                Attempt(
                    mailing=mailing,
                    status=Attempt.SUCCESS,
                    server_response=f"Отправлено писем: {sent}",
                )
            )
            success_count += 1
        except Exception as error:
            attempts.append(
                Attempt(
                    mailing=mailing,
                    status=Attempt.FAILED,
                    server_response=str(error),
                )
            )
            fail_count += 1

    Attempt.objects.bulk_create(attempts)
    mailing.update_status()
    return success_count, fail_count