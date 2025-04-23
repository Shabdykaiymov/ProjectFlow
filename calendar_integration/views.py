from rest_framework import views, status, permissions
from rest_framework.response import Response
from django.shortcuts import redirect
from django.conf import settings
from datetime import datetime
from .services import GoogleCalendarService
from accounts.models import UserProfile


class GoogleAuthURLView(views.APIView):
    """
    Представление для получения URL для авторизации в Google Calendar
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        auth_url, state = GoogleCalendarService.get_authorization_url(request)

        # Сохраняем состояние в сессии для проверки при callback
        request.session['google_auth_state'] = state
        print(f"Сохраняем состояние в сессии: {state}")

        # Явно сохраняем сессию
        request.session.save()

        return Response({'auth_url': auth_url})


class GoogleAuthCallbackView(views.APIView):
    """
    Представление для обработки callback от Google OAuth2
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        code = request.GET.get('code')
        state = request.GET.get('state')
        session_state = request.session.get('google_auth_state')

        print(f"Полученное состояние: {state}")
        print(f"Состояние в сессии: {session_state}")

        # Временно отключим проверку состояния для отладки
        # if state != session_state:
        #     return Response({'error': 'Неверное состояние'}, status=status.HTTP_400_BAD_REQUEST)

        # Обмениваем код на токены
        try:
            token_info = GoogleCalendarService.exchange_code_for_token(code)
            print(f"Получены токены: {token_info}")

            # Сохраняем токены в профиле пользователя
            user_profile = request.user.profile
            user_profile.google_calendar_token = token_info['token']
            user_profile.google_calendar_refresh_token = token_info.get('refresh_token')

            if token_info.get('expiry'):
                user_profile.google_calendar_token_expiry = datetime.fromisoformat(token_info['expiry'])

            user_profile.save()
            print(f"Токены сохранены для пользователя {request.user.username}")

            # Проверяем, был ли сохранен ID задачи перед авторизацией
            task_id = request.session.get('after_auth_task_id')
            if task_id:
                # Удаляем сохраненный ID из сессии
                del request.session['after_auth_task_id']
                print(f"Перенаправление на синхронизацию задачи {task_id}")
                # Перенаправляем на страницу синхронизации задачи
                return redirect(f'/api/tasks/{task_id}/sync_calendar/')

            # Перенаправляем на страницу успеха
            print("Перенаправление на страницу успеха")
            return redirect('/api/calendar/success/')

        except Exception as e:
            print(f"Ошибка при обработке callback: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

def get(self, request):
    # Получаем код авторизации из запроса
    code = request.GET.get('code')
    state = request.GET.get('state')

    # Проверяем состояние для безопасности
    if state != request.session.get('google_auth_state'):
        return Response({'error': 'Неверное состояние'}, status=status.HTTP_400_BAD_REQUEST)

    # Обмениваем код на токены
    try:
        token_info = GoogleCalendarService.exchange_code_for_token(code)

        # Сохраняем токены в профиле пользователя
        user_profile = request.user.profile
        user_profile.google_calendar_token = token_info['token']
        user_profile.google_calendar_refresh_token = token_info.get('refresh_token')

        if token_info.get('expiry'):
            user_profile.google_calendar_token_expiry = datetime.fromisoformat(token_info['expiry'])

        user_profile.save()

        # Проверяем, был ли сохранен ID задачи перед авторизацией
        task_id = request.session.get('after_auth_task_id')
        if task_id:
            # Удаляем сохраненный ID из сессии
            del request.session['after_auth_task_id']

            # Перенаправляем на страницу синхронизации задачи
            return redirect(f'/api/tasks/{task_id}/sync_calendar/')

        # Перенаправляем на страницу успеха
        return redirect('/api/calendar/success/')

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class GoogleCalendarSuccessView(views.APIView):
    """
    Представление для подтверждения успешной авторизации
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({
            'success': True,
            'message': 'Авторизация в Google Calendar успешно завершена'
        })