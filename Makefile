.PHONY: help build load deploy test clean

help: ## 显示可用命令
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## 构建前后端 Docker 镜像
	docker build -t bookstore-backend:dev ./src/backend
	docker build -t bookstore-frontend:dev ./src/frontend

load: build ## 加载镜像到 Minikube 容器运行时
	eval $$(minikube docker-env)
	docker build -t bookstore-backend:dev ./src/backend
	docker build -t bookstore-frontend:dev ./src/frontend

deploy: ## 应用 K8s 清单（Minikube 环境）
	kubectl apply -k k8s/overlays/minikube

test: ## 验证集群健康状态
	kubectl get pods -l app.kubernetes.io/part-of=bookstore
	kubectl rollout status deployment/bookstore-backend -w

clean: ## 清理部署资源
	kubectl delete -k k8s/overlays/minikube