from django.urls import path
from .views import (
    TasksByStatusView,
    TasksByUserView,
    ProjectProgressView
)

urlpatterns = [
    # URL для получения статистики задач по статусам
    path('tasks-by-status/', TasksByStatusView.as_view(), name='tasks_by_status'),

    # URL для получения статистики задач по пользователям
    path('tasks-by-user/', TasksByUserView.as_view(), name='tasks_by_user'),

    # URL для получения прогресса по проекту
    path('project-progress/<int:project_id>/', ProjectProgressView.as_view(), name='project_progress'),
]