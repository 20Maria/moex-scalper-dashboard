@echo off
chcp 65001 >nul
echo.
echo ============================================
echo   MOEX Scalper Dashboard - Запуск сервера
echo ============================================
echo.

REM Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден!
    echo.
    echo Пожалуйста, установите Python с сайта:
    echo https://www.python.org/downloads/
    echo.
    echo При установке обязательно отметьте галочку:
    echo "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

REM Проверка наличия API ключа
if not exist "api_key.txt" (
    echo [ВНИМАНИЕ] Файл api_key.txt не найден!
    echo.
    echo Создайте файл api_key.txt и вставьте туда ваш MOEX API ключ.
    echo.
    echo Без API ключа данные будут с задержкой 14 дней.
    echo.
    choice /C YN /M "Продолжить без API ключа?"
    if errorlevel 2 exit /b 0
)

echo [OK] Python найден
echo [OK] Запуск сервера...
echo.
echo Сервер запустится на порту 8081
echo Откройте в браузере: http://localhost:8081/scalper-dashboard.html
echo.
echo Нажмите Ctrl+C для остановки сервера
echo ============================================
echo.

python server.py

echo.
echo ============================================
echo Сервер остановлен
echo ============================================
pause
