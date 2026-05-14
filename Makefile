.PHONY: help build load deploy test clean scan

help: ## 显示可用命令
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## 构建前后端 Docker 镜像
	docker build -t bookstore-backend:dev ./src/backend
	docker build -t bookstore-frontend:dev ./src/frontend

load: build ## 加载镜像到 Minikube 容器运行时（解决 shell 隔离：使用 minikube image load）
	minikube image load bookstore-backend:dev
	minikube image load bookstore-frontend:dev
	@echo "✅ Images loaded into Minikube. Run 'kubectl rollout restart deployment/...' to pick up new images."

deploy: ## 应用 K8s 清单（Minikube 环境）
	kubectl apply -k k8s/overlays/minikube

test: ## 验证集群健康状态
	kubectl get pods -l app.kubernetes.io/part-of=bookstore -n bookstore
	kubectl rollout status deployment/bookstore-backend -n bookstore -w

clean: ## 清理部署资源
	kubectl delete -k k8s/overlays/minikube

scan: ## 容器安全扫描（需安装 Trivy: https://aquasecurity.github.io/trivy/)
	@echo "🔒 Scanning backend image..."
	@which trivy >/dev/null 2>&1 || (echo "❌ trivy not found. Install: https://aquasecurity.github.io/trivy/v0.18.3/installation/" && exit 1)
	trivy image --severity HIGH,CRITICAL --exit-code 0 bookstore-backend:dev
	@echo "🔒 Scanning frontend image..."
	trivy image --severity HIGH,CRITICAL --exit-code 0 bookstore-frontend:dev
