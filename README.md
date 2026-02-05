[![Main foodgram workflow](https://github.com/skevni/foodgram/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/skevni/foodgram/actions/workflows/main.yml)

# Foodgram — кулинарная книга для поваров и не только

## Описание проекта

Проект позволяет пользователям создавать, хранить и публиковать рецепты в на сайте, предварительно зарегистрировавшись на портале.  
Можно делиться рецептами, подписывать на рецепты других участников и добавлять блюда в избранное.  
Есть возможность составить список рецептов и скачать список продуктов, используемых в рецептах. Ингредиенты не повторяются, количество по ингредиентам суммируется.

## Возможности

- Регистрация и авторизация пользователей
- Создание и редактирование рецептов
- Список избранных рецептов
- Просмотр рецептов других пользователей
- Подписка на рецепты других пользователей
- Выгрузка списка ингредиентов для рецепта.

## Ссылки

- [Ссылка на развернутый проект](https://foodgramskevni.webhop.me/) - для ознакомления
- [Справка по API (Redoc)](https://foodgramskevni.webhop.me/api/docs/) — документация к API, примеры запросов и ответов.
- [Админка Django](https://foodgramskevni.webhop.me/admin/) — интерфейс управления пользователями, рецептами, тегами и ингредиентами.  

## Установка в docker окружении

_Примечание: Все примеры указаны для Linux_

1. Склонируйте репозиторий на свой компьютер:

    ```bash
    git clone https://github.com/skevni/foodgram.git
    ```

2. Передите в склонированный проект

    ```bash
    cd foodgram
    ```

3. Создайте файл `.env` и заполните его своими данными. Все необходимые переменные перечислены в файле `.env.example`, находящемся в корневой директории проекта.

4. Разверните приложение:

    ```bash
    sudo docker-compose -f docker-compose.production.yml up -d
    ```

5. Выполните миграции, соберите статические файлы бэкенда и скопируйте их в `/backend_static/static/`:

    ```bash
    sudo docker-compose -f docker-compose.production.yml exec backend python manage.py migrate
    sudo docker-compose -f docker-compose.production.yml exec backend python manage.py collectstatic
    sudo docker-compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
    ```

6. Добавьте ингредиенты и теги в базу данных

    ```bash
    sudo docker compose -f docker-compose.production.yml exec backend python manage.py load_tags_json
    sudo docker compose -f docker-compose.production.yml exec backend python manage.py load_ingredients_json
    ```

## Запуск проекта локально

_Примечание: Все примеры указаны для Linux_

1. Склонируйте репозиторий на свой компьютер:

    ```bash
    git clone https://github.com/skevni/foodgram.git
    cd foodgram
    ```

2. Создайте виртуальное окружение:

    ```bash
    python3 -m venv venv
    ```

3. Активируйте виртуальное окружение:

    ```bash
    source venv/bin/activate
    ```

4. Установите зависимости:

    ```bash
    cd backend
    pip install -r requirements.txt
    ```

5. Создайте файл `.env` и заполните его своими данными. Все необходимые переменные перечислены в файле `.env.example`, находящемся в корневой директории проекта.

6. Создайте структуру базы данных, применяя миграции:

    ```bash
    python3 manage.py migrate
    ```

7. Загружаем ингредиенты и теги в базу данных

    ```bash
    python3 manage.py load_tags_json
    python3 manage.py load_ingredients_json
    ```

8. Для входа в админ панель создайте учётную запись администратора

    ```bash
    python3 manage.py createsuperuser
    ```

9. Запустите сервер:

    ```bash
    python3 manage.py runserver
    ```

## Технологии

- Python
- Django
- Django REST Framework (DRF)
- Djoser
- PostgreSQL
- SQLite
- Gunicorn
- Nginx
- Docker
- Docker compose

## Архитектура

Проект разделён на три основных сервиса в Docker:

- foodgram_backend — Django + DRF API
- foodgram_frontend — фронтенд (статический сайт)
- foodgram_gateway — Nginx как шлюз и прокси

## Автор

[Евгений Скляров](https://github.com/skevni)

[Email](mailto:skevni@yandex.ru)

[Telegram](https://t.me/sklyaroven)
