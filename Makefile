.PHONY: help build build-backend build-frontend load load-backend load-frontend deploy deploy-tag test clean scan status

# 可覆盖的变量
VERSION     ?= dev
BACKEND_IMG  = bookstore-backend
FRONTEND_IMG = bookstore-frontend
OVERLAY_DIR  = k8s/overlays/minikube

help: ## 显示可用命令
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ================= 构建 =================
build: build-backend build-frontend ## 构建前后端 Docker 镜像

build-backend: ## 构建后端镜像（VERSION 可覆盖）
	docker build \
		--build-arg PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ \
		-t $(BACKEND_IMG):$(VERSION) ./src/backend

build-frontend: ## 构建前端镜像（VERSION 可覆盖）
	docker build -t $(FRONTEND_IMG):$(VERSION) ./src/frontend

# ================= 加载到 Minikube =================
load: load-backend load-frontend update-tags ## 构建、加载镜像并自动更新 kustomization tag

load-backend: build-backend ## 加载后端镜像到 Minikube
	minikube image load $(BACKEND_IMG):$(VERSION)

load-frontend: build-frontend ## 加载前端镜像到 Minikube
	minikube image load $(FRONTEND_IMG):$(VERSION)

update-tags: ## 自动更新 overlay 中的镜像 tag
	@echo "📝 Updating $(OVERLAY_DIR)/kustomization.yaml ..."
	@if command -v kustomize >/dev/null 2>&1; then \
		kustomize edit set image $(BACKEND_IMG)=$(BACKEND_IMG):$(VERSION) $(FRONTEND_IMG)=$(FRONTEND_IMG):$(VERSION); \
	else \
		sed -i "/name: $(BACKEND_IMG)$$/,/newTag:/{s/newTag: .*/newTag: $(VERSION)/}" $(OVERLAY_DIR)/kustomization.yaml; \
		sed -i "/name: $(FRONTEND_IMG)$$/,/newTag:/{s/newTag: .*/newTag: $(VERSION)/}" $(OVERLAY_DIR)/kustomization.yaml; \
	fi
	@echo "✅ Tags updated to $(VERSION)"

# ================= 部署 =================
deploy: ## 应用 K8s 清单（Minikube 环境）
	kubectl apply -k $(OVERLAY_DIR)

deploy-tag: load deploy ## 一键构建→加载→更新tag→部署
	@echo "🚀 Deployment complete with version $(VERSION)"

# ================= 验证 =================
test: ## 验证集群健康状态
	@echo "📊 Pod Status"
	kubectl get pods -l app.kubernetes.io/part-of=bookstore -n bookstore
	@echo ""
	@echo "⏳ Waiting for backend rollout..."
	kubectl rollout status deployment/bookstore-backend -n bookstore
	@echo ""
	@echo "🔗 Frontend URL:"
	minikube service bookstore-frontend --url -n bookstore || true

status: ## 快速查看所有组件状态
	@echo "=== Pods ==="
	kubectl get pods -n bookstore
	@echo ""
	@echo "=== Services ==="
	kubectl get svc -n bookstore
	@echo ""
	@echo "=== HPA ==="
	kubectl get hpa -n bookstore
	@echo ""
	@echo "=== Ingress ==="
	kubectl get ingress -n bookstore

# ================= 清理 =================
clean: ## 清理部署资源
	kubectl delete -k $(OVERLAY_DIR)

# ================= 安全扫描 =================
scan: ## 容器安全扫描（需安装 Trivy）
	@which trivy >/dev/null 2>&1 || (echo "❌ trivy not found. Install: https://aquasecurity.github.io/trivy/" && exit 1)
	@echo "🔒 Scanning backend image ($(BACKEND_IMG):$(VERSION))..."
	trivy image --severity HIGH,CRITICAL --exit-code 0 $(BACKEND_IMG):$(VERSION)
	@echo "🔒 Scanning frontend image ($(FRONTEND_IMG):$(VERSION))..."
	trivy image --severity HIGH,CRITICAL --exit-code 0 $(FRONTEND_IMG):$(VERSION)
