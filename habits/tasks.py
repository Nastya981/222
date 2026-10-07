import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .models import Habit
from .services import send_telegram_message

logger = logging.getLogger(__name__)


@shared_task
def check_habits_for_reminders():
    """
    Каждую минуту проверяет привычки, время которых совпадает с текущим,
    и отправляет напоминания в Telegram.
    """
    now = timezone.localtime()
    start = (now - timedelta(seconds=30)).time()
    end = (now + timedelta(seconds=30)).time()

    habits = Habit.objects.filter(time__range=(start, end)).select_related('user')

    sent = 0
    for habit in habits:
        chat_id = getattr(habit.user, 'telegram_chat_id', None)
        if not chat_id:
            logger.info('У пользователя %s нет telegram_chat_id', habit.user.email)
            continue

        text = (
            f'⏰ Напоминание о привычке:\n'
            f'<b>{habit.action}</b>\n'
            f'Место: {habit.place}\n'
            f'Время: {habit.time.strftime("%H:%M")}'
        )

        if send_telegram_message(chat_id, text):
            sent += 1

    logger.info('Отправлено %s напоминаний', sent)
    return f'Sent {sent} reminders'