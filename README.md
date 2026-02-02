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

## Установка

<i>Примечание: Все примеры указаны для Linux</i><br>

1. Склонируйте репозиторий на свой компьютер:

    ```bash
    git clone https://github.com/skevni/foodgram.git
    ```

2. Создайте файл `.env` и заполните его своими данными. Все необходимые переменные перечислены в файле `.env.example`, находящемся в корневой директории проекта.

### Создание Docker-образов

1. Замените `USERNAME` на свой логин на DockerHub:

    ``` bash
    cd frontend
    docker build -t USERNAME/foodgram_frontend .
    cd ../backend
    docker build -t USERNAME/foodgram_backend .
    cd ../nginx
    docker build -t USERNAME/foodgram_gateway . 
    ```

2. Загрузите образы на DockerHub:

    ```bash
    docker push USERNAME/foodgram_frontend
    docker push USERNAME/foodgram_backend
    docker push USERNAME/foodgram_gateway
    ```

### Деплой на сервере

1. Подключитесь к удаленному серверу

    ```bash
    ssh -i PATH_TO_SSH_KEY/SSH_KEY_NAME USERNAME@SERVER_IP_ADDRESS 
    ```

2. Создайте на сервере директорию `foodgram`:

    ```bash
    mkdir foodgram
    ```

3. Установите Docker Compose на сервер:

    ```bash
    sudo apt update
    sudo apt install curl
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo apt install docker-compose
    ```

4. Скопируйте файлы `docker-compose.production.yml` и `.env` в директорию `foodgram/` на сервере:

    ```bash
    scp -i PATH_TO_SSH_KEY/SSH_KEY_NAME docker-compose.production.yml USERNAME@SERVER_IP_ADDRESS:/home/USERNAME/foodgram/docker-compose.production.yml
    ```

    Где:
    - `PATH_TO_SSH_KEY` - путь к файлу с вашим SSH-ключом
    - `SSH_KEY_NAME` - имя файла с вашим SSH-ключом
    - `USERNAME` - ваше имя пользователя на сервере
    - `SERVER_IP_ADDRESS` - IP-адрес вашего сервера

5. Запустите Docker Compose в режиме демона:

    ```bash
    sudo docker-compose -f /home/USERNAME/foodgram/docker-compose.production.yml up -d
    ```

6. Выполните миграции, соберите статические файлы бэкенда и скопируйте их в `/backend_static/static/`:

    ```bash
    sudo docker-compose -f /home/USERNAME/foodgram/docker-compose.production.yml exec backend python manage.py migrate
    sudo docker-compose -f /home/USERNAME/foodgram/docker-compose.production.yml exec backend python manage.py collectstatic
    sudo docker-compose -f /home/USERNAME/foodgram/docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
    ```

7. Откройте конфигурационный файл Nginx в редакторе nano:

    ```bash
    sudo nano /etc/nginx/sites-enabled/default
    ```

8. Измените настройки `location` в секции `server`:

    ```bash
    location / {
        proxy_set_header Host $http_host;
        proxy_pass http://127.0.0.1:9000;
    }
    ```

9. Проверьте правильность конфигурации Nginx:

    ```bash
    sudo nginx -t
    ```

    Если вы получаете следующий ответ, значит, ошибок нет:

    ```bash
    nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
    nginx: configuration file /etc/nginx/nginx.conf test is successful
    ```

10. Перезапустите Nginx:

    ```bash
    sudo service nginx reload
    ```

## Настройка CI/CD

1. Файлы workflow уже написаны и находятся в директории:

    ```bash
    foodgram/.github/workflows/main.yml
    foodgram/.github/workflows/test.yml
    ```

    При пуше в любую ветку будут запускаться только тесты backend и frontend.
    А при пуше в ветку main будут запускаться тесты и деплой на удаленный сервер, при условии успешного выполнения тестов.

2. Для адаптации его к вашему серверу добавьте секреты в GitHub Actions:

    ```bash
    DOCKER_USERNAME                # имя пользователя в DockerHub
    DOCKER_PASSWORD                # пароль пользователя в DockerHub
    HOST                           # IP-адрес сервера
    USER                           # имя пользователя
    SSH_KEY                        # содержимое приватного SSH-ключа (cat ~/.ssh/id_rsa)
    SSH_PASSPHRASE                 # пароль для SSH-ключа
    POSTGRES_USER                  # имя пользователя для подключения к БД
    POSTGRES_PASSWORD              # пароль пользователя для подключения к БД
    POSTGRES_DB                    # имя БД

    TELEGRAM_TO                    # ID вашего телеграм-аккаунта (можно узнать у @userinfobot, команда /start)
    TELEGRAM_TOKEN                 # токен вашего бота (получить токен можно у @BotFather, команда /token, имя бота)
    ```

## Технологии

- Python
- Django
- Django REST Framework (DRF)
- Djoser
- PostgreSQL
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

[Evgenii Skliarov - skevni](https://github.com/skevni)
