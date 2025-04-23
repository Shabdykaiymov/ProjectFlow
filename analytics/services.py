from django.db.models import Count, Q
from tasks.models import Task
from projects.models import Project
from django.utils import timezone
from datetime import timedelta


class AnalyticsService:
    """
    Сервис для генерации аналитики по проектам и задачам
    """

    @staticmethod
    def get_tasks_by_status(user, project_id=None):
        """
        Получает статистику задач по статусам для всех проектов пользователя
        или для конкретного проекта
        """
        # Получаем все проекты пользователя
        projects = Project.objects.filter(members=user)

        # Базовый запрос
        tasks_query = Task.objects.filter(project__in=projects)

        # Если указан ID проекта, фильтруем по нему
        if project_id:
            tasks_query = tasks_query.filter(project_id=project_id)

        # Получаем статистику по статусам задач
        status_counts = tasks_query.values('status').annotate(count=Count('id'))

        # Преобразуем в словарь для удобства
        result = {
            'labels': [],
            'data': [],
            'backgroundColor': []
        }

        # Цвета для графиков
        colors = {
            'Новая': 'rgba(54, 162, 235, 0.6)',
            'В работе': 'rgba(255, 206, 86, 0.6)',
            'На проверке': 'rgba(75, 192, 192, 0.6)',
            'Завершена': 'rgba(153, 102, 255, 0.6)'
        }

        # Заполняем результат
        for status_item in status_counts:
            status = status_item['status']
            count = status_item['count']

            result['labels'].append(status)
            result['data'].append(count)
            result['backgroundColor'].append(colors.get(status, 'rgba(201, 203, 207, 0.6)'))

        return result

    @staticmethod
    def get_tasks_by_user(project_id=None, user=None):
        """
        Получает статистику задач по пользователям для проекта или всех проектов
        """
        # Базовый запрос
        query = Task.objects

        # Фильтрация по проекту, если указан
        if project_id:
            query = query.filter(project_id=project_id)
        elif user:
            # Если проект не указан, но указан пользователь,
            # фильтруем по проектам, где пользователь является участником
            query = query.filter(project__members=user)

        # Получаем статистику по исполнителям
        user_counts = query.values(
            'assignee__id',
            'assignee__username',
            'assignee__first_name',
            'assignee__last_name'
        ).annotate(count=Count('id'))

        # Преобразуем в формат для графика
        result = {
            'labels': [],
            'data': [],
            'backgroundColor': []
        }

        # Генерируем цвета для каждого пользователя
        import random

        for user_item in user_counts:
            # Пропускаем записи с None в assignee__id (задачи без исполнителя)
            if user_item['assignee__id'] is None:
                continue

            # Формируем имя пользователя
            first_name = user_item['assignee__first_name'] or ''
            last_name = user_item['assignee__last_name'] or ''
            username = user_item['assignee__username'] or ''

            if first_name or last_name:
                name = f"{first_name} {last_name}".strip()
            else:
                name = username

            result['labels'].append(name)
            result['data'].append(user_item['count'])

            # Генерируем случайный цвет
            color = f"rgba({random.randint(0, 255)}, {random.randint(0, 255)}, {random.randint(0, 255)}, 0.6)"
            result['backgroundColor'].append(color)

        return result

    @staticmethod
    def get_project_progress(project_id):
        """
        Получает данные о прогрессе проекта
        """
        try:
            project = Project.objects.get(id=project_id)

            # Получаем количество задач по статусам
            status_counts = Task.objects.filter(
                project=project
            ).values('status').annotate(count=Count('id'))

            # Преобразуем в словарь
            counts = {}
            total = 0

            for item in status_counts:
                counts[item['status']] = item['count']
                total += item['count']

            # Вычисляем проценты
            result = {
                'total_tasks': total,
                'completed_tasks': counts.get('Завершена', 0),
                'progress_percentage': 0
            }

            if total > 0:
                result['progress_percentage'] = round((counts.get('Завершена', 0) / total) * 100)

            return result
        except Project.DoesNotExist:
            return {
                'total_tasks': 0,
                'completed_tasks': 0,
                'progress_percentage': 0
            }