# src/backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# psycopg2-binary 使用预编译 wheel，无需编译器

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# 创建非 root 用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["python3", "-u", "main.py"]