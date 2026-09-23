FROM python:3.12-slim
WORKDIR /app
RUN pip install uv==0.5.11
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev
COPY services/api services/api
CMD ["uv","run","uvicorn","intentledger.main:app","--app-dir","services/api","--host","127.0.0.1","--port","8000"]
