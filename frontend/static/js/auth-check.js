// Проверка авторизации на защищенных страницах
(function() {
    // Пропускаем страницы авторизации
    if (window.location.pathname.includes('/login') ||
        window.location.pathname.includes('/register') ||
        window.location.pathname.includes('/admin')) {
        return;
    }

    // Проверяем наличие токена
    const token = localStorage.getItem('access_token');
    if (!token) {
        console.log("Нет токена, перенаправляем на логин");
        window.location.href = '/login/';
        return;
    }

    // Проверяем валидность токена
    fetch('/api/auth/me/', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    }).then(response => {
        if (!response.ok) {
            console.log("Токен недействителен, перенаправляем на логин");
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login/';
        } else {
            // Токен действителен, обновляем информацию о пользователе
            response.json().then(userData => {
                const usernameElement = document.getElementById('currentUsername');
                if (usernameElement) {
                    let displayName = userData.username;
                    if (userData.first_name || userData.last_name) {
                        displayName = `${userData.first_name || ''} ${userData.last_name || ''}`.trim();
                    }

                    usernameElement.textContent = displayName;
                }

                document.getElementById('userAuthenticatedMenu').style.display = 'block';
                document.getElementById('userGuestMenu').style.display = 'none';
            });
        }
    }).catch(error => {
        console.error("Ошибка при проверке токена:", error);
    });
})();