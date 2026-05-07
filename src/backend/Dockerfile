# src/backend/Dockerfile - 修复版
FROM python:3.11-slim
WORKDIR /app
COPY main.py .

# ✅ 显式创建 UID=1000 的用户，与 K8s securityContext 匹配
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

USER appuser
EXPOSE 8000
CMD ["python3", "-u", "main.py"]