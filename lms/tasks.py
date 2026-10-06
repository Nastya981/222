from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta

from .models import Course, Subscription

User = get_user_model()


@shared_task
def send_course_update_email(course_id: int):
    """Отправляет письма подписчикам курса при его обновлении."""
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return f'Course {course_id} not found'

    subscribers = Subscription.objects.filter(course=course).select_related('user')

    sent = 0
    for sub in subscribers:
        send_mail(
            subject=f'Обновление курса: {course.name}',
            message=f'Курс "{course.name}" был обновлён. Проверьте новые материалы.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[sub.user.email],
            fail_silently=True,
        )
        sent += 1

    return f'Sent {sent} emails for course {course_id}'


@shared_task
def deactivate_inactive_users():
    """Блокирует пользователей, не заходивших более месяца."""
    threshold = timezone.now() - timedelta(days=30)
    inactive = User.objects.filter(
        is_active=True,
        last_login__lt=threshold,
    )
    count = inactive.count()
    inactive.update(is_active=False)
    return f'Deactivated {count} users'