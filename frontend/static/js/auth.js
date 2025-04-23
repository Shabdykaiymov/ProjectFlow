/**
 * Модуль для работы с аутентификацией
 */

// Базовый URL API
const API_URL = '/api';

// Функция для проверки токена
async function checkToken() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
            window.location.href = '/login/';
        }
        return false;
    }

    try {
        const response = await fetch(`${API_URL}/auth/me/`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            return true;
        } else {
            // Если токен недействителен, очищаем хранилище и перенаправляем на страницу входа
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');

            if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
                window.location.href = '/login/';
            }
            return false;
        }
    } catch (error) {
        console.error('Ошибка при проверке токена:', error);
        return false;
    }
}

/**
 * Обновляет информацию о текущем пользователе в интерфейсе
 */

// Добавьте в начало функции updateUserInfo()
async function updateUserInfo() {
    try {
        // Проверяем, авторизован ли пользователь
        const token = localStorage.getItem('access_token');
        if (!token) {
            return;
        }

        // Выполняем запрос к API для получения информации о пользователе
        const response = await fetch(`${API_URL}/auth/me/`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error('Не удалось получить информацию о пользователе');
        }

        const userData = await response.json();

        // Обновляем информацию о пользователе на странице
        const usernameElement = document.getElementById('currentUsername');
        if (usernameElement) {
            // Определяем имя для отображения - предпочитаем имя и фамилию, если есть
            let displayName = userData.username;
            if (userData.first_name || userData.last_name) {
                displayName = `${userData.first_name || ''} ${userData.last_name || ''}`.trim();
            }

            usernameElement.textContent = displayName;
        }

        // Показываем меню для авторизованного пользователя
        document.getElementById('userAuthenticatedMenu').style.display = 'block';
        document.getElementById('userGuestMenu').style.display = 'none';
    } catch (error) {
        console.error('Ошибка при получении информации о пользователе:', error);
        // При ошибке показываем меню для гостя
        document.getElementById('userAuthenticatedMenu').style.display = 'none';
        document.getElementById('userGuestMenu').style.display = 'block';
    }
}

/**
 * Выполняет выход пользователя из системы
 */
async function logout() {
    try {
        const refreshToken = localStorage.getItem('refresh_token');

        if (refreshToken) {
            try {
                await fetch(`${API_URL}/auth/logout/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                    },
                    body: JSON.stringify({ refresh: refreshToken }),
                });
            } catch (e) {
                console.error('Ошибка при отправке запроса на выход:', e);
            }
        }

        // Очищаем локальное хранилище
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_key');

        // Перенаправляем на страницу входа
        window.location.href = '/login/';
        return false;
    } catch (error) {
        console.error('Ошибка при выходе:', error);
        // В любом случае очищаем хранилище и перенаправляем
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_key');
        window.location.href = '/login/';
        return false;
    }
}

// В обработчик события DOMContentLoaded
document.addEventListener('DOMContentLoaded', function() {
    // Проверяем авторизацию
    checkToken();

    // Если пользователь авторизован, обновляем информацию
    if (localStorage.getItem('access_token')) {
        updateUserInfo();
    }

    // Добавляем обработчик для кнопки выхода
    const logoutLink = document.getElementById('logoutLink');
    if (logoutLink) {
        logoutLink.addEventListener('click', function(e) {
            e.preventDefault();
            logout();
        });
    }
});