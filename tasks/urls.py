from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet

# Создаем router для ViewSet
router = DefaultRouter()
router.register(r'', TaskViewSet, basename='task')

urlpatterns = [
    # Подключаем все URL из router
    path('', include(router.urls)),
]