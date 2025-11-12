#!/bin/bash

echo "Установка зависимостей для парсера отзывов..."
echo

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    echo "ОШИБКА: Python 3 не найден! Установите Python 3.7 или выше."
    exit 1
fi

echo "Создание виртуального окружения..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "ОШИБКА: Не удалось создать виртуальное окружение"
    exit 1
fi

echo "Активация виртуального окружения..."
source venv/bin/activate

echo "Установка зависимостей..."
pip install --upgrade pip
pip install -r core/requirements.txt

if [ $? -ne 0 ]; then
    echo "ОШИБКА: Не удалось установить зависимости"
    exit 1
fi

echo
echo "========================================"
echo "Установка завершена успешно!"
echo "========================================"
echo
echo "Для активации виртуального окружения выполните:"
echo "  source venv/bin/activate"
echo
echo "Для запуска парсера:"
echo "  python main.py"
echo
