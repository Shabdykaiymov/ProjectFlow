from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.contrib.auth.models import User
from rest_framework.exceptions import NotFound, PermissionDenied
from .models import Project
from .serializers import ProjectSerializer, ProjectCreateSerializer, ProjectUpdateSerializer, ProjectMemberSerializer
from tasks.models import Task
from tasks.serializers import TaskSerializer
from .serializers import ProjectMemberActionSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления проектами
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Возвращает только проекты, в которых пользователь является участником
        """
        user = self.request.user
        return Project.objects.filter(members=user).order_by('-created_at')

    def get_serializer_class(self):
        """
        Возвращает соответствующий сериализатор в зависимости от действия
        """
        if self.action == 'create':
            return ProjectCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ProjectUpdateSerializer
        return ProjectSerializer

    def perform_create(self, serializer):
        """
        При создании проекта устанавливаем текущего пользователя как создателя
        """
        serializer.save()

    def get_serializer_context(self):
        """
        Передаем request в контекст сериализатора
        """
        context = super().get_serializer_context()
        return context

    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        """
        Получение всех задач проекта
        """
        project = self.get_object()
        tasks = Task.objects.filter(project=project)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def kanban(self, request, pk=None):
        """
        Получение задач проекта, сгруппированных по статусам для канбан-доски
        """
        project = self.get_object()

        # Получаем все возможные статусы задач
        statuses = dict(Task.STATUS_CHOICES)

        # Создаем структуру данных для канбан-доски
        kanban_data = {}
        for status_key, status_name in Task.STATUS_CHOICES:
            tasks = Task.objects.filter(project=project, status=status_key)
            kanban_data[status_key] = {
                'name': status_name,
                'tasks': TaskSerializer(tasks, many=True).data
            }

        return Response(kanban_data)

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """
        Добавляет участника в проект
        """
        project = self.get_object()

        # Проверяем, является ли текущий пользователь создателем проекта
        if project.created_by != request.user:
            raise PermissionDenied("Только создатель проекта может добавлять участников")

        # Используем сериализатор
        serializer = ProjectMemberActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Получаем ID или username пользователя из запроса
        user_id = serializer.validated_data.get('user_id')
        username = serializer.validated_data.get('username')

        try:
            if user_id:
                user = User.objects.get(id=user_id)
            else:
                user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise NotFound("Пользователь не найден")

        # Добавляем пользователя как участника
        project.members.add(user)

        return Response({"success": f"Пользователь {user.username} добавлен в проект"})

    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        """
        Удаляет участника из проекта
        """
        project = self.get_object()

        # Проверяем, является ли текущий пользователь создателем проекта
        if project.created_by != request.user:
            raise PermissionDenied("Только создатель проекта может удалять участников")

        # Используем сериализатор
        serializer = ProjectMemberActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Получаем ID или username пользователя из запроса
        user_id = serializer.validated_data.get('user_id')
        username = serializer.validated_data.get('username')

        try:
            if user_id:
                user = User.objects.get(id=user_id)
            else:
                user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise NotFound("Пользователь не найден")

        # Проверяем, что пользователь не удаляет сам себя
        if user == project.created_by:
            return Response(
                {"error": "Нельзя удалить создателя проекта из участников"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Удаляем пользователя из участников
        project.members.remove(user)

        return Response({"success": f"Пользователь {user.username} удален из проекта"})

    @action(detail=False, methods=['get'])
    def all_users(self, request):
        """
        Возвращает список всех пользователей для выбора участников проекта
        """
        users = User.objects.all()
        serializer = ProjectMemberSerializer(users, many=True)
        return Response(serializer.data)

