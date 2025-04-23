from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Project

class ProjectMemberSerializer(serializers.ModelSerializer):
    """Сериализатор для участников проекта (упрощенная версия User)"""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class ProjectSerializer(serializers.ModelSerializer):
    """Сериализатор для проектов с базовой информацией"""
    created_by = ProjectMemberSerializer(read_only=True)
    members = ProjectMemberSerializer(many=True, read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'created_by',
            'members', 'created_at', 'updated_at',
            'progress_percentage', 'task_count'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_progress_percentage(self, obj):
        """Получить процент выполнения проекта"""
        return obj.get_progress_percentage()

    def get_task_count(self, obj):
        """Получить количество задач в проекте"""
        return obj.get_task_count()


class ProjectCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания проектов"""
    member_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True
    )

    class Meta:
        model = Project
        fields = ['name', 'description', 'member_ids']

    def create(self, validated_data):
        # Извлекаем список ID пользователей, если он есть
        member_ids = validated_data.pop('member_ids', [])

        # Получаем текущего пользователя из контекста
        current_user = self.context['request'].user

        # Создаем проект
        project = Project.objects.create(
            created_by=current_user,
            **validated_data
        )

        # Добавляем создателя проекта как участника
        project.members.add(current_user)

        # Добавляем остальных участников, если они существуют
        if member_ids:
            existing_users = User.objects.filter(id__in=member_ids)
            for user in existing_users:
                project.members.add(user)

        return project

class ProjectMemberActionSerializer(serializers.Serializer):
        """Сериализатор для добавления/удаления участников проекта"""
        user_id = serializers.IntegerField(required=False)
        username = serializers.CharField(required=False)

        def validate(self, attrs):
            if not attrs.get('user_id') and not attrs.get('username'):
                raise serializers.ValidationError({"error": "Необходимо указать user_id или username"})
            return attrs


class ProjectUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления проектов"""
    member_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True
    )

    class Meta:
        model = Project
        fields = ['name', 'description', 'member_ids']

    def update(self, instance, validated_data):
        # Извлекаем список ID пользователей, если он есть
        member_ids = validated_data.pop('member_ids', None)

        # Обновляем поля проекта
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.save()

        # Обновляем список участников, если он был предоставлен
        if member_ids is not None:
            # Сначала очищаем существующих участников, кроме создателя
            instance.members.clear()
            instance.members.add(instance.created_by)

            # Добавляем новых участников
            existing_users = User.objects.filter(id__in=member_ids)
            for user in existing_users:
                instance.members.add(user)

        return instance