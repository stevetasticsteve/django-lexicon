FROM python:3.13
RUN apt-get update
RUN apt-get install -y hunspell-tools

RUN useradd django
EXPOSE 8010
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 \
    PORT=8000
WORKDIR /app
RUN chown django:django /app

RUN pip install psycopg2-binary gunicorn
COPY ./requirements.txt /
RUN pip install -r /requirements.txt
COPY --chown=django:django . .

USER django
RUN mkdir -p /app/data/exports
RUN mkdir -p /app/data/logs
RUN python manage.py collectstatic --noinput --clear --settings config.settings.prod
CMD set -xe; python manage.py  migrate --settings config.settings.prod; gunicorn config.wsgi:application --timeout 60 --access-logfile /app/data/logs/requests.log --error-logfile /app/data/logs/gunicorn_errors.log
