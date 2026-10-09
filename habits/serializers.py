from rest_framework import serializers

from .models import Habit
from .validators import (
    validate_reward_or_related,
    validate_duration,
    validate_related_habit_is_pleasant,
    validate_pleasant_habit,
    validate_periodicity,
)


class HabitSerializer(serializers.ModelSerializer):
    """Сериализатор привычки."""
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Habit
        fields = (
            'id', 'user', 'place', 'time', 'action',
            'is_pleasant', 'related_habit', 'periodicity',
            'reward', 'duration', 'is_public', 'created_at',
        )
        read_only_fields = ('id', 'user', 'created_at')

    def validate(self, attrs):
        # Собираем итоговый state: то, что пришло в запросе, + то, что уже было в объекте
        instance = self.instance
        data = dict(attrs)

        if instance is not None:
            # Для обновления: недостающие поля берём из существующего объекта
            for field in ('is_pleasant', 'related_habit', 'reward', 'duration', 'periodicity'):
                if field not in data:
                    data[field] = getattr(instance, field)

        # 1. reward XOR related_habit
        validate_reward_or_related(data)

        # 2. duration <= 120
        validate_duration(data.get('duration'))

        # 3. related_habit должна быть приятной
        validate_related_habit_is_pleasant(data.get('related_habit'))

        # 4. у приятной привычки не должно быть reward/related
        validate_pleasant_habit(data)

        # 5. periodicity 1..7
        validate_periodicity(data.get('periodicity'))

        # 6. related_habit должна принадлежать тому же пользователю
        related = data.get('related_habit')
        if related is not None and self.context.get('request'):
            user = self.context['request'].user
            if related.user_id != user.id:
                raise serializers.ValidationError(
                    {'related_habit': 'Связанная привычка должна принадлежать вам.'}
                )

        # 7. related_habit не может ссылаться сама на себя
        if instance is not None and related is not None and related.id == instance.id:
            raise serializers.ValidationError(
                {'related_habit': 'Привычка не может быть связана сама с собой.'}
            )

        return attrs

    def validate_related_habit(self, value):
        # Отдельная проверка на уровне поля — если related_habit пришла
        if value is not None and self.context.get('request'):
            user = self.context['request'].user
            if value.user_id != user.id:
                raise serializers.ValidationError('Связанная привычка должна принадлежать вам.')
        return value

    def validate_duration(self, value):
        validate_duration(value)
        return value