from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet

# Создаем router для ViewSet
router = DefaultRouter()
router.register(r'', ProjectViewSet, basename='project')

# Добавляем дополнительные URL для действий
member_actions = [
    path('<int:pk>/add_member/', ProjectViewSet.as_view({'post': 'add_member'}), name='project-add-member'),
    path('<int:pk>/remove_member/', ProjectViewSet.as_view({'post': 'remove_member'}), name='project-remove-member'),
    path('all_users/', ProjectViewSet.as_view({'get': 'all_users'}), name='project-all-users'),
]

urlpatterns = [
    # Подключаем все URL из router
    path('', include(router.urls)),
    # Добавляем URL действий
    *member_actions,
]