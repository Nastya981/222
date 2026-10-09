# Habit Tracker (Курсовая работа)

Бэкенд SPA-приложения «Трекер полезных привычек» на Django REST Framework с уведомлениями в Telegram.

## Что умеет

- Регистрация и JWT-авторизация
- CRUD привычек с валидацией
- Публичные привычки (только чтение)
- Уведомления в Telegram по расписанию (Celery + Celery Beat)
- Пагинация (5 на страницу)
- Документация API (Swagger / ReDoc)

## Стек технологий

- **Backend:** Django 6.0, Django REST Framework
- **Авторизация:** JWT (djangorestframework-simplejwt)
- **БД:** PostgreSQL 14
- **Брокер/кэш:** Redis 7
- **Очередь задач:** Celery 5 + django-celery-beat
- **Web-сервер:** Nginx + Gunicorn
- **Контейнеризация:** Docker + Docker Compose
- **CI/CD:** GitHub Actions
- **Сервер:** VDSina (Ubuntu 22.04)

---

## Запуск локально

### 1. Клонировать репозиторий

    git clone https://github.com/Nastya981/222.git
    cd 222
    git checkout feature/docker-deploy

### 2. Создать файл .env

Скопируйте .env.docker в .env:

    cp .env.docker .env

Откройте .env и заполните переменные: SECRET_KEY, DEBUG, ALLOWED_HOSTS, DB_NAME, DB_USER, DB_PASSWORD, TELEGRAM_BOT_TOKEN.

Остальные переменные оставьте как в .env.docker.

### 3. Запустить проект одной командой

    docker compose up -d --build

Сборка займёт 3–7 минут. После запуска:

- Swagger UI: http://localhost/api/docs/
- Админка: http://localhost/admin/

### 4. Остановить проект

    docker compose down

---

## Деплой на удалённый сервер

Проект настроен на автоматический деплой через GitHub Actions при push в ветку feature/docker-deploy.

При каждом push запускается workflow:

1. test — запуск тестов Django
2. lint — проверка PEP 8 через flake8
3. build — сборка Docker-образов
4. deploy — SSH на сервер + docker compose up -d --build

Если тесты падают — деплой не выполняется.

### Секреты GitHub

В репозитории добавлены секреты:

- SSH_HOST — IP сервера (109.172.88.132)
- SSH_USER — пользователь SSH (root)
- SSH_KEY — приватный SSH-ключ для деплоя

---

## Сервисы в docker-compose

| Сервис | Образ | Назначение |
|---|---|---|
| db | postgres:14 | База данных |
| redis | redis:7-alpine | Брокер Celery |
| web | 222-web | Django + Gunicorn |
| celery-worker | 222-celery-worker | Обработка задач |
| celery-beat | 222-celery-beat | Планировщик |
| nginx | nginx:1.25-alpine | Reverse-proxy |

---

## Ссылки

- Сайт: http://109.172.88.132/
- Swagger: http://109.172.88.132/api/docs/
- ReDoc: http://109.172.88.132/api/redoc/
- Админка: http://109.172.88.132/admin/

---

## Тесты

    python manage.py test

Покрытие: ~93%.