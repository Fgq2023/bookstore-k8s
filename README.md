# ☁️ Cloud-Native Online Bookstore System (Kubernetes)

> DSAA4040 Engineering Track Project | Group 5

## 🚀 Quick Start
```bash
# 1. 启动 Minikube
minikube start --driver=docker --cpus=2 --memory=4096
minikube addons enable ingress metrics-server

# 2. 一键部署
make load deploy

# 3. 访问系统
minikube service bookstore-frontend --url

