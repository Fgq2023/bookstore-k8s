# src/frontend/Dockerfile
FROM nginx:1.25-alpine

# 删除默认配置
RUN rm -f /etc/nginx/conf.d/default.conf

# 复制自定义配置 + 静态文件
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html /usr/share/nginx/html/index.html

# ✅ 关键修复：预创建并授权所有 nginx 需要写入的路径
RUN mkdir -p /var/cache/nginx /var/log/nginx /var/run \
    && touch /var/run/nginx.pid \
    && chown -R nginx:nginx /var/cache/nginx /var/log/nginx /var/run/nginx.pid \
    && chmod -R 755 /var/cache/nginx /var/log/nginx /var/run/nginx.pid

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:80/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]