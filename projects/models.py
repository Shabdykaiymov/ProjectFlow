from django.db import models
from django.contrib.auth.models import User


class Project(models.Model):
    """
    Модель для хранения информации о проектах
    """
    name = models.CharField(max_length=100, verbose_name="Название проекта")
    description = models.TextField(blank=True, verbose_name="Описание проекта")

    # Связь с создателем проекта
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_projects',
        verbose_name="Создатель проекта"
    )

    # Участники проекта (многие-ко-многим)
    members = models.ManyToManyField(
        User,
        related_name='projects',
        blank=True,
        verbose_name="Участники проекта"
    )

    # Дата и время создания/обновления
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_task_count(self):
        """Получить количество задач в проекте"""
        return self.tasks.count()

    def get_completed_task_count(self):
        """Получить количество завершенных задач"""
        return self.tasks.filter(status='Завершена').count()

    def get_progress_percentage(self):
        """Получить процент выполнения проекта"""
        total = self.get_task_count()
        if total == 0:
            return 0
        return int((self.get_completed_task_count() / total) * 100)