@echo off
chcp 65001 >nul
title API Сервер парсера отзывов

echo ========================================
echo    API СЕРВЕР ПАРСЕРА ОТЗЫВОВ
echo ========================================
echo.

REM Переходим в корневую папку проекта
cd /d "%~dp0\.."

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден! Установите Python 3.7+
    echo Скачать можно с: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python найден
echo.

REM Устанавливаем зависимости
echo 📦 Установка зависимостей...
pip install -r core/requirements.txt --quiet

if errorlevel 1 (
    echo ❌ Ошибка установки зависимостей
    pause
    exit /b 1
)

echo ✅ Зависимости установлены
echo.

echo 🚀 Запуск API сервера...
echo.
echo API будет доступен по адресу: http://localhost:8000
echo Документация: http://localhost:8000/docs
echo.
echo Нажмите Ctrl+C для остановки
echo.

python api/api_server.py

pause
