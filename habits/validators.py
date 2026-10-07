from django.core.exceptions import ValidationError


def validate_reward_or_related(value):
    """Нельзя одновременно указывать и вознаграждение, и связанную привычку."""
    reward = value.get('reward')
    related = value.get('related_habit')
    if reward and related:
        raise ValidationError(
            'Нельзя одновременно указывать вознаграждение и связанную привычку.'
        )


def validate_duration(value):
    """Время выполнения — не больше 120 секунд."""
    if value is not None and value > 120:
        raise ValidationError('Время выполнения не может превышать 120 секунд.')


def validate_related_habit_is_pleasant(value):
    """В связанные привычки можно привязать только приятную привычку."""
    if value and not value.is_pleasant:
        raise ValidationError('Связанная привычка должна быть приятной.')


def validate_pleasant_habit(value):
    """У приятной привычки не может быть вознаграждения или связанной привычки."""
    is_pleasant = value.get('is_pleasant')
    reward = value.get('reward')
    related = value.get('related_habit')
    if is_pleasant and (reward or related):
        raise ValidationError(
            'У приятной привычки не может быть вознаграждения или связанной привычки.'
        )


def validate_periodicity(value):
    """Периодичность — от 1 до 7 дней."""
    if value is not None and (value < 1 or value > 7):
        raise ValidationError('Периодичность должна быть от 1 до 7 дней.')