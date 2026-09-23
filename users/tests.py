from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse


class RegistrationTests(TestCase):
    def test_registration_creates_inactive_user(self) -> None:
        response = self.client.post(
            reverse("users:register"),
            {
                "email": "student@example.com",
                "password1": "Strong-password-123",
                "password2": "Strong-password-123",
            },
        )

        user = get_user_model().objects.get(email="student@example.com")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)