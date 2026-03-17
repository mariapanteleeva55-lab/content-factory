@echo off
echo Запуск Content Factory...

:: Запускаем Redis
start "Redis" cmd /k "redis-server"

:: Даём Redis секунду запуститься
timeout /t 2 /nobreak >nul

:: Запускаем бэкенд
start "Backend" cmd /k "cd /d "%~dp0backend" && venv\Scripts\activate && python main.py"

:: Запускаем Celery воркер
start "Celery Worker" cmd /k "cd /d "%~dp0backend" && venv\Scripts\activate && python -m celery -A tasks worker --loglevel=info -P solo"

:: Даём бэкенду 3 секунды запуститься
timeout /t 3 /nobreak >nul

:: Запускаем фронтенд
start "Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

:: Открываем браузер
timeout /t 5 /nobreak >nul
start http://localhost:3001

echo.
echo Всё запущено! Браузер откроется автоматически.
echo Чтобы остановить — закрой все открывшиеся окна.
