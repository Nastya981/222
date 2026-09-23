from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from mailing.models import Attempt, Mailing, Message, Recipient
from mailing.services import send_mailing


class MailingTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            email="owner@example.com",
            password="strong-password",
        )
        self.other_user = user_model.objects.create_user(
            email="other@example.com",
            password="strong-password",
        )
        self.recipient = Recipient.objects.create(
            owner=self.owner,
            email="client@example.com",
            full_name="Получатель",
        )
        self.message = Message.objects.create(
            owner=self.owner,
            subject="Тема",
            body="Текст",
        )
        self.mailing = Mailing.objects.create(
            owner=self.owner,
            message=self.message,
            start_time=timezone.now() - timedelta(minutes=1),
            end_time=timezone.now() + timedelta(minutes=10),
        )
        self.mailing.recipients.add(self.recipient)

    def test_send_mailing_creates_attempt(self) -> None:
        success_count, fail_count = send_mailing(self.mailing)

        self.assertEqual(success_count, 1)
        self.assertEqual(fail_count, 0)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(Attempt.objects.count(), 1)
        self.assertEqual(mail.outbox[0].to, ["client@example.com"])

    def test_user_cannot_update_someone_elses_recipient(self) -> None:
        self.client.force_login(self.other_user)
        response = self.client.get(
            reverse(
                "mailing:recipient_update",
                args=[self.recipient.pk],
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_home_statistics_are_cached(self) -> None:
        cache.clear()
        self.client.force_login(self.owner)

        response = self.client.get(reverse("mailing:home"))

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(cache.get(f"home-stats:{self.owner.pk}:0"))