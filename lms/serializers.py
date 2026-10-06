from rest_framework import serializers
from .models import Course, Lesson, Subscription
from .validators import validate_youtube_url


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = '__all__'
        read_only_fields = ('owner',)
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Lesson.objects.all(),
                fields=('name', 'course'),
                message='Урок с таким названием уже есть в этом курсе.',
            ),
        ]

    def validate_video_link(self, value):
        validate_youtube_url(value)
        return value


class CourseSerializer(serializers.ModelSerializer):
    lessons_count = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = (
            'id', 'name', 'preview', 'description',
            'lessons_count', 'lessons', 'owner', 'is_subscribed',
        )
        read_only_fields = ('owner',)

    def get_lessons_count(self, obj):
        return obj.lessons.count()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Subscription.objects.filter(user=request.user, course=obj).exists()