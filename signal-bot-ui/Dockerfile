FROM python:3.11-slim AS builder
RUN pip install --no-cache-dir poetry==1.8.3
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry export --without-hashes -f requirements.txt -o requirements.txt

FROM python:3.11-slim
RUN useradd --system --create-home --shell /usr/sbin/nologin uiuser
WORKDIR /app
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=uiuser:uiuser . .
USER uiuser
EXPOSE 5001
CMD ["python", "app.py"]
