from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import HabitViewSet, PublicHabitViewSet

router = DefaultRouter()
router.register(r'habits', HabitViewSet, basename='habit')

urlpatterns = [
    # ВАЖНО: этот маршрут ДО include(router.urls),
    # иначе /habits/public/ уйдёт в /habits/{pk}/ и вернёт 404
    path(
        'habits/public/',
        PublicHabitViewSet.as_view({'get': 'list'}),
        name='public-habit-list',
    ),
    path('', include(router.urls)),
]