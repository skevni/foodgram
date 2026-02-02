FROM python:3.13-slim
WORKDIR /app
COPY ./requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
COPY . .
# Запуск сервера в dev режиме
# CMD [ "python", "manage.py", "runserver", "0:8000" ]
CMD [ "gunicorn", "--bind", "0.0.0.0:8000", "backend.wsgi" ]
