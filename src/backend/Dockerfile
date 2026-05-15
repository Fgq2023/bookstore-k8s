# src/backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# psycopg2-binary 使用预编译 wheel，无需编译器

# 安装 Python 依赖
COPY requirements.txt .
ARG PIP_INDEX_URL=https://pypi.org/simple
RUN pip install --no-cache-dir -r requirements.txt -i ${PIP_INDEX_URL} --timeout 120

COPY main.py .
COPY alembic.ini .
COPY alembic/ ./alembic/

# 创建非 root 用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["python3", "-u", "main.py"]