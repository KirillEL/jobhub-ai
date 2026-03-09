FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PYTHONPATH=/app/src

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

COPY src /app/src
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini
COPY README.md /app/README.md

EXPOSE 8000

CMD ["uvicorn", "parser_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
