from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Task, Comment
from projects.models import Project


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для представления пользователя в задаче"""

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class TaskSerializer(serializers.ModelSerializer):
    """Сериализатор для задач"""
    project_name = serializers.SerializerMethodField()
    assignee = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    is_overdue = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority', 'project', 'project_name',
            'assignee', 'assignee_id', 'created_by', 'due_date', 'created_at',
            'updated_at', 'google_calendar_event_id', 'is_overdue', 'comments_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'is_overdue', 'comments_count']
        extra_kwargs = {
            'assignee_id': {'write_only': True, 'source': 'assignee', 'required': False},
            'google_calendar_event_id': {'read_only': True}
        }

    def get_project_name(self, obj):
        """Возвращает название проекта"""
        return obj.project.name if obj.project else None

    def get_is_overdue(self, obj):
        """Проверяет, просрочена ли задача"""
        return obj.is_overdue()

    def get_comments_count(self, obj):
        """Возвращает количество комментариев к задаче"""
        return obj.comments.count()

    def validate_project(self, value):
        """Проверяет, имеет ли пользователь доступ к проекту"""
        user = self.context['request'].user
        if not value.members.filter(id=user.id).exists():
            raise serializers.ValidationError("У вас нет доступа к этому проекту")
        return value

    def validate_assignee_id(self, value):
        """Проверяет, является ли назначаемый пользователь участником проекта"""
        if value:
            project_id = self.initial_data.get('project')
            if project_id:
                try:
                    project = Project.objects.get(id=project_id)
                    if not project.members.filter(id=value.id).exists():
                        raise serializers.ValidationError(
                            "Исполнитель должен быть участником проекта"
                        )
                except Project.DoesNotExist:
                    pass
        return value

    def create(self, validated_data):
        # Устанавливаем текущего пользователя как создателя
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class CommentSerializer(serializers.ModelSerializer):
    """Сериализатор для комментариев к задачам"""
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'task', 'author', 'author_name', 'text', 'created_at']
        read_only_fields = ['id', 'author', 'created_at']

    def get_author_name(self, obj):
        """Возвращает имя автора комментария"""
        if obj.author.first_name or obj.author.last_name:
            return f"{obj.author.first_name} {obj.author.last_name}".strip()
        return obj.author.username

    def create(self, validated_data):
        # Устанавливаем текущего пользователя как автора
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class TaskStatusUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления статуса задачи"""

    class Meta:
        model = Task
        fields = ['status']


class TaskPriorityUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления приоритета задачи"""

    class Meta:
        model = Task
        fields = ['priority']