import os
import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from django.conf import settings


class GoogleCalendarService:
    """
    Сервис для работы с Google Calendar API
    """
    # Области доступа (scopes), которые нам нужны
    SCOPES = ['https://www.googleapis.com/auth/calendar']

    @staticmethod
    def get_authorization_url(request):
        """
        Генерирует URL для авторизации пользователя через Google OAuth2
        """
        # Создаем объект Flow для OAuth2
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
                }
            },
            scopes=GoogleCalendarService.SCOPES
        )

        # Устанавливаем URI перенаправления
        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI

        # Генерируем URL авторизации
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Всегда запрашиваем refresh_token
        )

        return authorization_url, state

    @staticmethod
    def exchange_code_for_token(code):
        """
        Обменивает код авторизации на токены доступа
        """
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
                }
            },
            scopes=GoogleCalendarService.SCOPES
        )

        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI

        # Обмениваем код на токен
        flow.fetch_token(code=code)

        # Получаем учетные данные
        credentials = flow.credentials

        return {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None
        }