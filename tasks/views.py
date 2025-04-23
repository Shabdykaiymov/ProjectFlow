from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Task, Comment
from .serializers import (
    TaskSerializer, TaskStatusUpdateSerializer, TaskPriorityUpdateSerializer,
    CommentSerializer
)
from projects.models import Project


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления задачами
    """
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'due_date', 'priority', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Возвращает задачи, к которым у пользователя есть доступ
        """
        user = self.request.user

        # Получаем проекты, в которых пользователь является участником
        projects = Project.objects.filter(members=user)

        # Формируем базовый запрос
        queryset = Task.objects.filter(project__in=projects)

        # Фильтрация по проекту, если указан в запросе
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)

        # Фильтрация по статусу, если указан
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        # Фильтрация по приоритету, если указан
        priority_param = self.request.query_params.get('priority')
        if priority_param:
            queryset = queryset.filter(priority=priority_param)

        # Фильтрация по исполнителю (мои задачи)
        assigned_to_me = self.request.query_params.get('assigned_to_me')
        if assigned_to_me and assigned_to_me.lower() == 'true':
            queryset = queryset.filter(assignee=user)

        # Фильтрация по создателю (созданные мной)
        created_by_me = self.request.query_params.get('created_by_me')
        if created_by_me and created_by_me.lower() == 'true':
            queryset = queryset.filter(created_by=user)

        return queryset

    def perform_create(self, serializer):
        """
        При создании задачи устанавливаем текущего пользователя как создателя
        """
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['patch'])
    def status(self, request, pk=None):
        """
        Обновление статуса задачи
        """
        task = self.get_object()
        serializer = TaskStatusUpdateSerializer(task, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'])
    def priority(self, request, pk=None):
        """
        Обновление приоритета задачи
        """
        task = self.get_object()
        serializer = TaskPriorityUpdateSerializer(task, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """
        Получение комментариев к задаче
        """
        task = self.get_object()
        comments = Comment.objects.filter(task=task)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """
        Добавление комментария к задаче
        """
        task = self.get_object()
        serializer = CommentSerializer(data={
            'task': task.id,
            'text': request.data.get('text')
        }, context={'request': request})

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def sync_calendar(self, request, pk=None):
        """
        Синхронизация задачи с Google Calendar
        """
        task = self.get_object()

        # Проверяем, есть ли у пользователя токен Google Calendar
        user_profile = request.user.profile
        if not user_profile.google_calendar_token:
            # Если токена нет, сохраняем ID задачи в сессии и перенаправляем на страницу авторизации
            request.session['after_auth_task_id'] = str(task.id)
            return Response({
                'status': 'redirect',
                'url': '/api/calendar/auth-url/'
            })

        try:
            # Импортируем необходимые библиотеки
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            from datetime import datetime, timedelta
            from django.conf import settings

            # Создаем объект credentials из сохраненных токенов
            credentials = Credentials(
                token=user_profile.google_calendar_token,
                refresh_token=user_profile.google_calendar_refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET,
                scopes=['https://www.googleapis.com/auth/calendar']
            )

            # Создаем сервис Google Calendar
            service = build('calendar', 'v3', credentials=credentials)

            # Формируем данные для события
            event_summary = f"[ProjectFlow] {task.title}"
            event_description = task.description or "Без описания"

            # Определяем время начала и окончания события
            start_time = task.due_date if task.due_date else datetime.now() + timedelta(days=1)
            end_time = start_time + timedelta(hours=1)

            # Форматируем время для Google Calendar API
            start_time_str = start_time.isoformat()
            end_time_str = end_time.isoformat()

            # Создаем событие
            event = {
                'summary': event_summary,
                'description': event_description,
                'start': {
                    'dateTime': start_time_str,
                    'timeZone': 'Asia/Bishkek',  # Используйте ваш часовой пояс
                },
                'end': {
                    'dateTime': end_time_str,
                    'timeZone': 'Asia/Bishkek',  # Используйте ваш часовой пояс
                },
                'reminders': {
                    'useDefault': True
                },
            }

            # Если уже есть ID события, обновляем его, иначе создаем новое
            if task.google_calendar_event_id:
                updated_event = service.events().update(
                    calendarId='primary',
                    eventId=task.google_calendar_event_id,
                    body=event
                ).execute()
                event_id = updated_event['id']
                action = 'обновлено'
            else:
                created_event = service.events().insert(
                    calendarId='primary',
                    body=event
                ).execute()
                event_id = created_event['id']
                action = 'создано'

            # Сохраняем ID события в задаче
            task.google_calendar_event_id = event_id
            task.save()

            return Response({
                'status': 'success',
                'message': f'Событие успешно {action} в Google Calendar',
                'event_id': event_id,
                'event_link': created_event.get('htmlLink')
            })

        except Exception as e:
            import traceback
            print(f"Ошибка при синхронизации с Google Calendar: {str(e)}")
            print(traceback.format_exc())
            return Response({
                'status': 'error',
                'message': f'Ошибка при синхронизации с Google Calendar: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)