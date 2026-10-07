from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from habits.models import Habit
from habits.validators import (
    validate_reward_or_related,
    validate_duration,
    validate_periodicity,
)

User = get_user_model()


class BaseHabitTestCase(APITestCase):
    """Общий setUp: создаём двух пользователей и привычку."""

    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@test.com',
            password='testpass123',
            telegram_chat_id='111111111',
        )
        self.other = User.objects.create_user(
            email='other@test.com',
            password='testpass123',
        )
        self.habit = Habit.objects.create(
            user=self.owner,
            place='Дом',
            time='08:00:00',
            action='Выпить воду',
            is_pleasant=False,
            periodicity=1,
            duration=60,
            is_public=False,
        )


class UserRegistrationTestCase(APITestCase):
    """Тесты регистрации пользователя."""

    def test_register_user(self):
        url = reverse('users:register')
        data = {
            'email': 'newuser@test.com',
            'password': 'Str0ngPass!23',
            'password_confirm': 'Str0ngPass!23',
            'telegram_chat_id': '999888777',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], 'newuser@test.com')
        self.assertEqual(response.data['telegram_chat_id'], '999888777')

    def test_register_password_mismatch(self):
        url = reverse('users:register')
        data = {
            'email': 'newuser2@test.com',
            'password': 'Str0ngPass!23',
            'password_confirm': 'DifferentPass!23',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email(self):
        User.objects.create_user(email='owner@test.com', password='SomePass123!')

        url = reverse('users:register')
        data = {
            'email': 'owner@test.com',
            'password': 'Str0ngPass!23',
            'password_confirm': 'Str0ngPass!23',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class JWTAuthTestCase(APITestCase):
    """JWT-логин."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='jwt@test.com',
            password='TestPass123!',
        )

    def test_login_success(self):
        url = reverse('users:login')
        response = self.client.post(
            url,
            {'email': 'jwt@test.com', 'password': 'TestPass123!'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_wrong_password(self):
        url = reverse('users:login')
        response = self.client.post(
            url,
            {'email': 'jwt@test.com', 'password': 'wrong'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class HabitCRUDTestCase(BaseHabitTestCase):
    """CRUD привычек + права доступа."""

    def test_list_unauthorized(self):
        response = self.client.get('/api/habits/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_owner(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get('/api/habits/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_create_habit(self):
        self.client.force_authenticate(user=self.owner)
        data = {
            'place': 'Спортзал',
            'time': '18:00:00',
            'action': 'Тренировка',
            'periodicity': 1,
            'duration': 60,
            'is_public': False,
        }
        response = self.client.post('/api/habits/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user'], self.owner.id)

    def test_retrieve_own_habit(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f'/api/habits/{self.habit.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_own_habit(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            f'/api/habits/{self.habit.id}/',
            {'action': 'Изменено'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.habit.refresh_from_db()
        self.assertEqual(self.habit.action, 'Изменено')

    def test_update_others_habit_forbidden(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.patch(
            f'/api/habits/{self.habit.id}/',
            {'action': 'Hack'},
            format='json',
        )
        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
        )

    def test_delete_own_habit(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.delete(f'/api/habits/{self.habit.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Habit.objects.filter(id=self.habit.id).exists())

    def test_delete_others_habit_forbidden(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.delete(f'/api/habits/{self.habit.id}/')
        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
        )


class PublicHabitTestCase(BaseHabitTestCase):
    """Публичные привычки."""

    def setUp(self):
        super().setUp()
        self.public_habit = Habit.objects.create(
            user=self.other,
            place='Парк',
            time='07:00:00',
            action='Прогулка',
            periodicity=1,
            duration=120,
            is_public=True,
        )

    def test_list_public_habits(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get('/api/habits/public/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['action'], 'Прогулка')

    def test_public_habit_read_only(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            f'/api/habits/public/{self.public_habit.id}/',
            {'action': 'Hack'},
            format='json',
        )
        self.assertIn(
            response.status_code,
            [
                status.HTTP_403_FORBIDDEN,
                status.HTTP_404_NOT_FOUND,
                status.HTTP_405_METHOD_NOT_ALLOWED,
            ],
        )


class HabitPaginationTestCase(BaseHabitTestCase):
    """Пагинация — 5 на страницу."""

    def test_pagination_5_per_page(self):
        for i in range(7):
            Habit.objects.create(
                user=self.owner,
                place=f'Место {i}',
                time='09:00:00',
                action=f'Действие {i}',
                periodicity=1,
                duration=30,
                is_public=False,
            )
        self.client.force_authenticate(user=self.owner)
        response = self.client.get('/api/habits/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)
        self.assertEqual(response.data['count'], 8)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)


class HabitValidatorsTestCase(APITestCase):
    """Проверка валидаторов."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='v@test.com',
            password='TestPass123!',
        )
        self.client.force_authenticate(user=self.user)

    def test_reward_and_related_conflict(self):
        pleasant = Habit.objects.create(
            user=self.user,
            place='X',
            time='10:00:00',
            action='Приятная',
            periodicity=1,
            duration=30,
            is_pleasant=True,
            is_public=False,
        )
        data = {
            'place': 'Дом',
            'time': '11:00:00',
            'action': 'Полезная',
            'periodicity': 1,
            'duration': 60,
            'reward': 'Мороженое',
            'related_habit': pleasant.id,
        }
        response = self.client.post('/api/habits/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duration_over_120(self):
        data = {
            'place': 'Дом',
            'time': '11:00:00',
            'action': 'Долгая',
            'periodicity': 1,
            'duration': 200,
        }
        response = self.client.post('/api/habits/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pleasant_with_reward_rejected(self):
        data = {
            'place': 'Дом',
            'time': '11:00:00',
            'action': 'Приятная',
            'periodicity': 1,
            'duration': 30,
            'is_pleasant': True,
            'reward': 'Что-то',
        }
        response = self.client.post('/api/habits/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_periodicity_out_of_range(self):
        data = {
            'place': 'Дом',
            'time': '11:00:00',
            'action': 'Редкая',
            'periodicity': 30,
            'duration': 30,
        }
        response = self.client.post('/api/habits/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_valid_direct_validators(self):
        validate_duration(120)
        validate_periodicity(7)
        with self.assertRaises(Exception):
            validate_duration(121)
        with self.assertRaises(Exception):
            validate_periodicity(8)
        with self.assertRaises(Exception):
            validate_periodicity(0)
        with self.assertRaises(Exception):
            validate_reward_or_related({'reward': 'X', 'related_habit': 'Y'})


class TelegramServiceTestCase(APITestCase):
    """Тесты сервиса отправки в Telegram."""

    @patch('habits.services.requests.post')
    def test_send_telegram_message_success(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        from habits.services import send_telegram_message

        with self.settings(TELEGRAM_BOT_TOKEN='fake-token'):
            result = send_telegram_message('123456789', 'Тест')
        self.assertTrue(result)
        mock_post.assert_called_once()

    @patch('habits.services.requests.post')
    def test_send_telegram_message_error(self, mock_post):
        mock_post.return_value = MagicMock(status_code=400, text='Bad Request')
        from habits.services import send_telegram_message

        with self.settings(TELEGRAM_BOT_TOKEN='fake-token'):
            result = send_telegram_message('123456789', 'Тест')
        self.assertFalse(result)

    def test_send_telegram_message_no_token(self):
        from habits.services import send_telegram_message

        with self.settings(TELEGRAM_BOT_TOKEN=''):
            result = send_telegram_message('123456789', 'Тест')
        self.assertFalse(result)

    def test_send_telegram_message_no_chat_id(self):
        from habits.services import send_telegram_message

        with self.settings(TELEGRAM_BOT_TOKEN='fake-token'):
            result = send_telegram_message('', 'Тест')
        self.assertFalse(result)


class CheckHabitsTaskTestCase(APITestCase):
    """Тесты Celery-задачи проверки привычек."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='task@test.com',
            password='TestPass123!',
            telegram_chat_id='555555555',
        )

    @patch('habits.tasks.send_telegram_message')
    def test_task_sends_reminder_for_matching_habit(self, mock_send):
        mock_send.return_value = True

        now_time = timezone.localtime().time()
        Habit.objects.create(
            user=self.user,
            place='Дом',
            time=now_time,
            action='Проверка',
            periodicity=1,
            duration=30,
            is_public=False,
        )

        from habits.tasks import check_habits_for_reminders
        result = check_habits_for_reminders()
        self.assertIn('Sent 1 reminders', result)
        mock_send.assert_called_once()

    @patch('habits.tasks.send_telegram_message')
    def test_task_skips_habit_without_chat_id(self, mock_send):
        user_no_chat = User.objects.create_user(
            email='nochat@test.com',
            password='TestPass123!',
            telegram_chat_id=None,
        )
        now_time = timezone.localtime().time()
        Habit.objects.create(
            user=user_no_chat,
            place='Дом',
            time=now_time,
            action='Без чата',
            periodicity=1,
            duration=30,
            is_public=False,
        )

        from habits.tasks import check_habits_for_reminders
        result = check_habits_for_reminders()
        self.assertIn('Sent 0 reminders', result)
        mock_send.assert_not_called()