from rest_framework import views, status, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from projects.models import Project
from .services import AnalyticsService


class TasksByStatusView(views.APIView):
    """
    Представление для получения статистики задач по статусам
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Получаем ID проекта из запроса, если он есть
        project_id = request.query_params.get('project_id')

        # Получаем статистику задач по статусам
        data = AnalyticsService.get_tasks_by_status(request.user, project_id)
        return Response(data)


class TasksByUserView(views.APIView):
    """
    Представление для получения статистики задач по пользователям
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Получаем ID проекта из запроса, если он есть
        project_id = request.query_params.get('project_id')

        # Если указан ID проекта, проверяем права доступа
        if project_id:
            try:
                project = Project.objects.get(id=project_id)
                if not project.members.filter(id=request.user.id).exists():
                    return Response(
                        {'error': 'У вас нет доступа к этому проекту'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Project.DoesNotExist:
                return Response(
                    {'error': 'Проект не найден'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Получаем статистику задач по пользователям для проекта
            data = AnalyticsService.get_tasks_by_user(project_id=project_id)
        else:
            # Получаем статистику задач по пользователям для всех проектов
            data = AnalyticsService.get_tasks_by_user(user=request.user)

        return Response(data)

class ProjectProgressView(views.APIView):
    """
    Представление для получения прогресса по проекту
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id):
        # Проверяем права доступа к проекту
        project = get_object_or_404(Project, id=project_id)
        if not project.members.filter(id=request.user.id).exists():
            return Response(
                {'error': 'У вас нет доступа к этому проекту'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Получаем данные о прогрессе проекта
        data = AnalyticsService.get_project_progress(project_id)
        return Response(data)