# ![Main Foodgram workflow](https://github.com/MoskvinaAnastasia/foodgram/actions/workflows/main.yml/badge.svg)

## Стек использованных технологий

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![Django REST Framework](https://img.shields.io/badge/Django%20REST%20Framework-ff1709?style=for-the-badge&logo=django&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-black?style=for-the-badge&logo=JSON%20web%20tokens)
![Djoser](https://img.shields.io/badge/Djoser-00ADD8?style=for-the-badge&logo=docker&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-269539?style=for-the-badge&logo=nginx&logoColor=white)
![Gunicorn](https://img.shields.io/badge/Gunicorn-499848?style=for-the-badge&logo=gunicorn&logoColor=white)

## Описание проекта

Проект «Фудграм» — сайт, на котором пользователи будут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также будет доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

Проект доступен по [адресу](https://nastuxa-foodgram.hopto.org/)

### Для неавторизованных пользователей доступно:
- Зарегистрироваться / создать аккаунт.
- Просматривать рецепты на главной странице.
- Просматривать отдельные страницы рецептов.
- Просматривать страницы пользователей.
- Фильтровать рецепты по тегам.

### Для авторизованных пользователей доступно:
- Авторизация в системе под своим логином и паролем.
- Выход из системы.
- Смена пароля.
- Создание/редактирование/удаление собственных рецептов.
- Просмотр рецептов на главной странице.
- Просмотр страницы пользователей.
- Фильтрация рецептов по тегам.
- Работа с персональным списком избранного: добавлять в него рецепты или удалять их, просматривать свою страницу избранных рецептов.
- Работа с персональным списком покупок: добавлять/удалять любые рецепты, выгружать файл с количеством необходимых ингредиентов для рецептов в списке покупок.
- Подписка на публикации авторов рецептов и отменить подписку, просматривать свою страницу подписок.

Администратор обладает всеми правами авторизованного пользователя. Плюсом он может:
- Изменять пароль любого пользователя.
- Создавать/блокировать/удалять аккаунты пользователей.
- Редактировать/удалять любые рецепты.
- Добавлять/удалять/редактировать теги.
- Добавлять/удалять ингредиенты.

## Как развернуть проект на удаленном сервере

1. Форкнуть репозиторий в свой GitHub и склонировать его:

    ```bash
    git clone https://github.com/<username>/foodgram
    ```

2. Добавить следующие secrets в settings своего репозитория:

    - `ALLOWED_HOSTS` # список хостов, которые могут отправлять запрос на бэкенд
    - `SECRET_KEY` # значение переменной SECRET_KEY
    - `DOCKER_NAME` # никнейм в DockerHub
    - `DOCKER_PASSWORD` # пароль пользователя в DockerHub
    - `DOCKER_USERNAME` # имя пользователя в DockerHub
    - `HOST` # IP-адрес удаленного сервера
    - `SETTINGS_DEBUG` # значение переменной SETTINGS True/False
    - `SSH_KEY` # приватный ssh-ключ сервера
    - `SSH_PASSPHRASE` # кодовая фраза (пароль) для ssh-ключа
    - `TELEGRAM_ID` # ID пользователя в Telegram
    - `TELEGRAM_TOKEN` # токен телеграм-бота
    - `USER` # логин на удаленном сервере

3. Создать Docker-образы

    ```bash
    cd foodgram
    cd frontend
    docker build -t username/foodgram-frontend .
    cd ../backend
    docker build -t username/foodgram-backend .
    ```

4. Загрузить образы на DockerHub

    ```bash
    docker push username/foodgram-frontend
    docker push username/foodgram-backend
    ```

5. Создать папку `foodgram` на вашем сервере и скопировать в нее:

    - `.env`, добавьте в него переменные из списка в файле `.env.example` в корне проекта
    - Создать папку `infra` в папке `foodgram` и скопировать в нее `docker-compose.production.yml`

6. Запустить docker compose в режиме демона:

    ```bash
    sudo docker compose -f docker-compose.production.yml up -d
    ```

7. Выполнить миграции, собрать статику бэкенда и скопировать их в `/static/static/`:

    ```bash
    sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
    sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic --no-input
    sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/staticfiles/. /static/static/
    sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /static/
    ```

8. Изменить конфиг Nginx в зависимости от имеющегося. Например:

    ```bash
    sudo nano /etc/nginx/sites-enabled/default
    ```

    ```nginx
    location / {
        proxy_set_header Host $http_host;
        proxy_pass http://127.0.0.1:8000;
    }
    ```

9. Проверить конфиг Nginx и перезапустить его:

    ```bash
    sudo nginx -t
    sudo service nginx reload
    ```

## Настройка CI/CD

1. Файл workflow уже написан. Он находится в директории

    ```text
    foodgram/.github/workflows/main.yml
    ```

2. После пуша в ветку `main` будут выполнены следующие джобы:

    - проверка кода на соответствие PEP8 (с помощью пакета flake8)
    - билд и пуш контейнеров frontend и backend на DockerHub
    - деплой на удаленный сервер
    - при успешном деплое отправка сообщения в Telegram с информацией о коммите

## Автор проекта
[MoskvinaAnastasia](https://github.com/MoskvinaAnastasia/)
