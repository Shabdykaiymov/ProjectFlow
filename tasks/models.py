from django.db import models
from django.contrib.auth.models import User
from projects.models import Project


class Task(models.Model):
    """
    Модель для хранения задач проекта
    """
    # Статусы задачи для канбан-доски
    STATUS_CHOICES = (
        ('Новая', 'Новая'),
        ('В работе', 'В работе'),
        ('На проверке', 'На проверке'),
        ('Завершена', 'Завершена'),
    )

    # Приоритеты задачи
    PRIORITY_CHOICES = (
        ('Критический', 'Критический'),
        ('Высокий', 'Высокий'),
        ('Средний', 'Средний'),
        ('Низкий', 'Низкий'),
        ('Без приоритета', 'Без приоритета'),
    )

    # Основная информация о задаче
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    description = models.TextField(blank=True, verbose_name="Описание")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Новая',
        verbose_name="Статус"
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='Без приоритета',
        verbose_name="Приоритет"
    )

    # Связи с проектом и пользователями
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name="Проект"
    )
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
        verbose_name="Исполнитель"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_tasks',
        verbose_name="Создатель"
    )

    # Даты
    due_date = models.DateTimeField(null=True, blank=True, verbose_name="Срок выполнения")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    # Поле для связи с Google Calendar
    google_calendar_event_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="ID события в Google Calendar"
    )

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def is_overdue(self):
        """Проверка, просрочена ли задача"""
        from django.utils import timezone
        if self.due_date and self.status != 'Завершена':
            return self.due_date < timezone.now()
        return False

    @property
    def comments_count(self):
        """Возвращает количество комментариев к задаче"""
        return self.comments.count()


class Comment(models.Model):
    """
    Модель для хранения комментариев к задачам
    """
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Задача"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='task_comments',
        verbose_name="Автор"
    )
    text = models.TextField(verbose_name="Текст комментария")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ['created_at']

    def __str__(self):
        return f"Комментарий от {self.author.username} к задаче {self.task.id}"