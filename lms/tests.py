from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from rest_framework import status
from rest_framework.test import APITestCase

from lms.models import Course, Lesson, Subscription

User = get_user_model()


class BaseTestCase(APITestCase):
    """Общий setUp для всех тестов."""

    def setUp(self):
        self.owner = User.objects.create_user(email='owner@test.com', password='pass12345')
        self.moderator = User.objects.create_user(email='mod@test.com', password='pass12345')
        self.other = User.objects.create_user(email='other@test.com', password='pass12345')

        mod_group, _ = Group.objects.get_or_create(name='moderators')
        self.moderator.groups.add(mod_group)

        self.course = Course.objects.create(name='Test Course', owner=self.owner)
        self.lesson = Lesson.objects.create(
            name='Test Lesson',
            course=self.course,
            owner=self.owner,
            video_link='https://youtube.com/watch?v=abc',
        )


class LessonCRUDTestCase(BaseTestCase):
    """CRUD уроков: права, валидация."""

    def test_create_lesson_valid_youtube(self):
        self.client.force_authenticate(user=self.owner)
        data = {'name': 'New Lesson', 'course': self.course.id, 'video_link': 'https://youtube.com/watch?v=xyz'}
        response = self.client.post('/api/lessons/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_lesson_invalid_url(self):
        self.client.force_authenticate(user=self.owner)
        data = {'name': 'Bad', 'course': self.course.id, 'video_link': 'https://example.com/video'}
        response = self.client.post('/api/lessons/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('youtube.com', str(response.data))

    def test_create_lesson_moderator_forbidden(self):
        self.client.force_authenticate(user=self.moderator)
        data = {'name': 'Mod Lesson', 'course': self.course.id}
        response = self.client.post('/api/lessons/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_lessons_unauthenticated(self):
        response = self.client.get('/api/lessons/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_lessons_authenticated(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get('/api/lessons/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_lesson(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f'/api/lessons/{self.lesson.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_lesson_by_owner(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(f'/api/lessons/{self.lesson.id}/', {'name': 'Updated'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.name, 'Updated')

    def test_update_lesson_by_other_forbidden(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.patch(f'/api/lessons/{self.lesson.id}/', {'name': 'Hack'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_lesson_by_moderator(self):
        self.client.force_authenticate(user=self.moderator)
        response = self.client.patch(f'/api/lessons/{self.lesson.id}/', {'name': 'Mod'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_lesson_by_owner(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.delete(f'/api/lessons/{self.lesson.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Lesson.objects.filter(id=self.lesson.id).exists())

    def test_delete_lesson_by_moderator_forbidden(self):
        self.client.force_authenticate(user=self.moderator)
        response = self.client.delete(f'/api/lessons/{self.lesson.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_lesson_by_other_forbidden(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.delete(f'/api/lessons/{self.lesson.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SubscriptionTestCase(BaseTestCase):
    """Подписка на курс."""

    def test_subscribe(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post('/api/subscribe/', {'course_id': self.course.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'подписка добавлена')
        self.assertTrue(Subscription.objects.filter(user=self.owner, course=self.course).exists())

    def test_unsubscribe(self):
        Subscription.objects.create(user=self.owner, course=self.course)
        self.client.force_authenticate(user=self.owner)
        response = self.client.post('/api/subscribe/', {'course_id': self.course.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'подписка удалена')
        self.assertFalse(Subscription.objects.filter(user=self.owner, course=self.course).exists())

    def test_subscribe_unauthenticated(self):
        response = self.client.post('/api/subscribe/', {'course_id': self.course.id})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_subscribe_course_not_found(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post('/api/subscribe/', {'course_id': 99999})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_course_contains_is_subscribed_flag(self):
        Subscription.objects.create(user=self.owner, course=self.course)
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f'/api/courses/{self.course.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_subscribed'])