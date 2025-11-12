# Инструкция по загрузке на GitHub

## Шаг 1: Проверка статуса

```bash
git status
```

## Шаг 2: Добавление всех файлов

```bash
git add .
```

## Шаг 3: Создание первого коммита

```bash
git commit -m "Initial commit: Парсер отзывов с Yandex карт и 2GIS"
```

## Шаг 4: Создание репозитория на GitHub

1. Перейдите на https://github.com
2. Нажмите кнопку **"New repository"** (или **"+"** → **"New repository"**)
3. Введите название репозитория (например: `reviews-parser`)
4. Выберите **Public** или **Private**
5. **НЕ** добавляйте README, .gitignore или LICENSE (они уже есть)
6. Нажмите **"Create repository"**

## Шаг 5: Подключение к GitHub

После создания репозитория GitHub покажет инструкции. Выполните:

```bash
# Добавьте remote (замените YOUR_USERNAME и YOUR_REPO на свои)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Или через SSH (если настроен):
# git remote add origin git@github.com:YOUR_USERNAME/YOUR_REPO.git
```

## Шаг 6: Загрузка на GitHub

```bash
# Переименуйте ветку в main (если нужно)
git branch -M main

# Загрузите код
git push -u origin main
```

## Проверка

После загрузки проверьте репозиторий на GitHub - все файлы должны быть там!

## Дальнейшая работа

### Обновление кода

```bash
# Добавить изменения
git add .

# Создать коммит
git commit -m "Описание изменений"

# Загрузить на GitHub
git push
```

### Создание новой ветки

```bash
git checkout -b feature/new-feature
# Внесите изменения
git add .
git commit -m "Добавлена новая функция"
git push -u origin feature/new-feature
```

## Полезные команды

```bash
# Просмотр истории коммитов
git log

# Просмотр статуса
git status

# Просмотр изменений
git diff

# Отмена изменений в файле
git checkout -- filename.py
```
