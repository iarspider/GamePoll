# syntax=docker/dockerfile:1.7

############################
# Base image & common ENV  #
############################
ARG PYTHON_VERSION=3.12-slim

FROM python:${PYTHON_VERSION} AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Создаём непривилегированного пользователя (настраиваемые UID/GID)
ARG APP_UID=10001
ARG APP_GID=10001
RUN groupadd -g ${APP_GID} app && useradd -u ${APP_UID} -g ${APP_GID} -m -s /bin/sh app

# Runtime-зависимости (минимум; libpq5 — для psycopg/psycopg2)
# Используем кэши apt для ускорения сборок
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && apt-get install -y --no-install-recommends \
      libpq5 curl ca-certificates tzdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

############################
# Builder: wheels          #
############################
FROM base AS builder

# Build deps только здесь
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && apt-get install -y --no-install-recommends \
      build-essential gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Ставим Poetry (пин версия для воспроизводимости)
ARG POETRY_VERSION=2.2.1
RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}" \
 && poetry self add poetry-plugin-export

# Копируем только метаданные проекта для лучшего кэширования
COPY pyproject.toml poetry.lock* /app/

# Экспорт зависимостей в requirements.txt без хешей (воспроизводимо и быстро)
RUN poetry export --format=requirements.txt --without-hashes -o /app/requirements.txt

# Собираем колёса всех зависимостей
RUN --mount=type=cache,target=/root/.cache/pip \
    pip wheel --no-deps --wheel-dir /wheels -r /app/requirements.txt

############################
# Final: runtime image     #
############################
FROM base AS final

# Копируем подготовленные колёса и ставим зависимости
COPY --from=builder /wheels /wheels
COPY --from=builder /app/requirements.txt /tmp/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-index --find-links=/wheels -r /tmp/requirements.txt \
    && rm -rf /wheels /tmp/requirements.txt

# Копируем исходники приложения (предполагается корректный .dockerignore)
COPY . /app

# Папки для статики/медиа/логов/БД (если монтируете с хоста — удобно)
RUN mkdir -p /app/static /app/media /app/logs /app/db \
    && chown -R app:app /app

USER app

EXPOSE 8000

# Healthcheck — простой эндпоинт, не требующий БД (например, /healthz)
HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
  CMD curl -fsS http://127.0.0.1:8000/healthz || exit 1

# Оставляю ваш entrypoint — он должен существовать и быть исполняемым
ENTRYPOINT ["/app/entrypoint.sh"]
