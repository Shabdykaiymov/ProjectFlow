from django.shortcuts import render, redirect

def index_view(request):
    """Главная страница - перенаправляет на список проектов для авторизованных
       или на страницу входа для неавторизованных"""
    return redirect('project_list')

def login_view(request):
    """Страница входа"""
    return render(request, 'accounts/login.html')

def register_view(request):
    """Страница регистрации"""
    return render(request, 'accounts/register.html')

def project_list_view(request):
    """Страница со списком проектов"""
    return render(request, 'projects/list.html')

def project_detail_view(request, project_id):
    """Страница проекта с канбан-доской"""
    return render(request, 'projects/detail.html', {'project_id': project_id})

def tasks_list_view(request):
    """Страница со списком задач"""
    return render(request, 'tasks/list.html')

def analytics_view(request):
    """Страница аналитики"""
    return render(request, 'analytics/index.html')

def profile_view(request):
    """Страница профиля пользователя"""
    return render(request, 'accounts/profile.html')

def logout_view(request):
    """
    Страница выхода из системы
    """
    from django.contrib.auth import logout
    logout(request)
    return redirect('login')

def test_view(request):
    """Тестовая страница для отладки"""
    return render(request, 'test.html')