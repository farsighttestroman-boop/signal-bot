FROM python:3.11-slim AS builder
RUN pip install --no-cache-dir poetry==1.8.3
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry export --without-hashes -f requirements.txt -o requirements.txt

FROM python:3.11-slim
RUN useradd --system --create-home --shell /usr/sbin/nologin signalbot
WORKDIR /app
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=signalbot:signalbot . .
USER signalbot
CMD ["python", "main.py"]
