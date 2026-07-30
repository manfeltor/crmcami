# CRM Intralog — imagen para Cloud Run.
# Single-stage: el SPA se sirve CRUDO (sin build de Node); solo Python +
# gunicorn + WhiteNoise para estaticos. Cloud Run hace de reverse proxy/TLS.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=crmcami.settings

# Dependencias del SO para compilar/usar mysqlclient
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential default-libmysqlclient-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# collectstatic en el build (WhiteNoise sirve desde staticfiles/). Las creds son
# dummy y SOLO para este RUN (no quedan en la imagen); collectstatic no toca la DB.
RUN SECRET_KEY=build DB_NAME=build DB_USR=build DB_PASS=build DB_PORT=3306 \
    python manage.py collectstatic --noinput

# Cloud Run inyecta $PORT. sh -c para expandir $PORT; exec para que gunicorn sea
# PID 1 y reciba bien las señales (SIGTERM del escalado a cero).
CMD ["sh", "-c", "exec gunicorn crmcami.wsgi:application --bind :${PORT:-8080} --workers 2 --threads 4 --timeout 60"]
