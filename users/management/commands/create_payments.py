from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from users.models import User, Payment
from lms.models import Course, Lesson


class Command(BaseCommand):
    help = 'Создаёт тестовые платежи'

    def handle(self, *args, **options):
        Payment.objects.all().delete()

        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR('Сначала создайте пользователя'))
            return

        course = Course.objects.first()
        lesson = Lesson.objects.first()

        if not course:
            self.stdout.write(self.style.ERROR('Сначала создайте курс'))
            return

        payments = [
            Payment(
                user=user,
                payment_date=timezone.now() - timedelta(days=10),
                course=course,
                amount=50000,
                payment_method=Payment.TRANSFER,
            ),
            Payment(
                user=user,
                payment_date=timezone.now() - timedelta(days=5),
                lesson=lesson,
                amount=5000,
                payment_method=Payment.CASH,
            ),
            Payment(
                user=user,
                payment_date=timezone.now(),
                course=course,
                amount=30000,
                payment_method=Payment.TRANSFER,
            ),
        ]

        Payment.objects.bulk_create(payments)
        self.stdout.write(self.style.SUCCESS(f'Создано {len(payments)} платежей'))
