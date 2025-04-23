from django.urls import path
from .views import (
    GoogleAuthURLView,
    GoogleAuthCallbackView,
    GoogleCalendarSuccessView
)

urlpatterns = [
    # URL для получения авторизационного URL
    path('auth-url/', GoogleAuthURLView.as_view(), name='google_auth_url'),

    # URL для обработки callback от Google OAuth2
    path('auth-callback/', GoogleAuthCallbackView.as_view(), name='google_auth_callback'),

    # URL для подтверждения успешной авторизации
    path('success/', GoogleCalendarSuccessView.as_view(), name='google_auth_success'),
]