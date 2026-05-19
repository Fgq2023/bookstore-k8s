.PHONY: help build build-backend build-frontend load load-backend load-frontend deploy deploy-monitoring deploy-tag test clean scan status load-test port-forward-prometheus port-forward-grafana

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

deploy-monitoring: ## 部署 Grafana Dashboard 到 monitoring namespace
	@echo "📊 Deploying Grafana dashboard..."
	kubectl apply -k k8s/monitoring/
	echo "✅ Dashboard deployed. Access Grafana: make port-forward-grafana"

deploy-tag: load deploy deploy-monitoring ## 一键构建→加载→更新tag→部署+监控
	@echo "🚀 Deployment complete with version $(VERSION)"

# ================= 测试 =================
test: ## 验证集群健康状态
	@echo "📊 Pod Status"
	kubectl get pods -l app.kubernetes.io/part-of=bookstore -n bookstore
	@echo ""
	@echo "⏳ Waiting for backend rollout..."
	kubectl rollout status deployment/bookstore-backend -n bookstore
	@echo ""
	@echo "🔗 Frontend URL:"
	minikube service bookstore-frontend --url -n bookstore || true

test-backend: ## 运行后端单元测试（mock DB）
	@echo "🧪 Running backend unit tests..."
	@cd src/backend && pytest tests/ -v -m "not integration and not e2e"

test-backend-integration: ## 运行后端集成测试（真实 PostgreSQL）
	@echo "🐘 Running backend integration tests with testcontainers..."
	@cd src/backend && pytest tests/integration/ tests/e2e/ -v

test-frontend: ## 运行前端单元测试
	@echo "🎨 Running frontend unit tests..."
	@cd src/frontend && npm run test

test-frontend-e2e: ## 运行前端 Playwright E2E 测试
	@echo "🎭 Running frontend E2E tests..."
	@cd src/frontend && npx playwright test

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

verify: ## 端到端验证（Pod 状态 + API 健康检查）
	@echo "🔍 Verifying deployment..."
	@kubectl get pods -n bookstore -l app.kubernetes.io/part-of=bookstore -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.phase}{"\n"}{end}'
	@echo ""
	@echo "🩺 Health checks..."
	@BACKEND_POD=$$(kubectl get pod -n bookstore -l app=bookstore-backend -o jsonpath='{.items[0].metadata.name}' 2>/dev/null); \
	if [ -n "$$BACKEND_POD" ]; then \
		echo "Backend /healthz: $$(kubectl exec -n bookstore $$BACKEND_POD -- wget -qO- http://localhost:8000/healthz 2>/dev/null || echo 'unavailable')"; \
		echo "Backend /ready:   $$(kubectl exec -n bookstore $$BACKEND_POD -- wget -qO- http://localhost:8000/ready 2>/dev/null || echo 'unavailable')"; \
	else \
		echo "❌ No backend pod found"; \
	fi
	@FRONTEND_POD=$$(kubectl get pod -n bookstore -l app=bookstore-frontend -o jsonpath='{.items[0].metadata.name}' 2>/dev/null); \
	if [ -n "$$FRONTEND_POD" ]; then \
		echo "Frontend /healthz: $$(kubectl exec -n bookstore $$FRONTEND_POD -- wget -qO- http://localhost:80/healthz 2>/dev/null || echo 'unavailable')"; \
	else \
		echo "❌ No frontend pod found"; \
	fi
	@echo ""
	@echo "✅ Verification complete"

# ================= 清理 =================
clean: ## 清理部署资源
	kubectl delete -k $(OVERLAY_DIR)

# ================= 监控访问 =================
port-forward-prometheus: ## 端口转发 Prometheus UI (localhost:9090)
	@echo "📊 Prometheus: http://localhost:9090"
	kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090

port-forward-grafana: ## 端口转发 Grafana UI (localhost:3000)
	@echo "📈 Grafana: http://localhost:3000 (admin / $$(kubectl get secret -n monitoring prometheus-grafana -o jsonpath='{.data.admin-password}' | base64 -d 2>/dev/null || echo 'see secret'))"
	kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80

# ================= 性能测试 =================
LOADTEST_URL ?= http://$$(minikube ip)

load-test: ## 运行 k6 负载测试（通过 Docker）
	@echo "⚡ Starting k6 load test against $(LOADTEST_URL)"
	@docker run --rm -i --network=host \
		-v "$(PWD)/scripts:/scripts" \
		grafana/k6:latest run /scripts/loadtest.js \
		-e BASE_URL=$(LOADTEST_URL) \
		|| echo "❌ k6 failed. Ensure Docker is running."

# ================= 安全扫描 =================
scan: ## 容器安全扫描（需安装 Trivy）
	@which trivy >/dev/null 2>&1 || (echo "❌ trivy not found. Install: https://aquasecurity.github.io/trivy/" && exit 1)
	@echo "🔒 Scanning backend image ($(BACKEND_IMG):$(VERSION))..."
	trivy image --severity HIGH,CRITICAL --exit-code 0 $(BACKEND_IMG):$(VERSION)
	@echo "🔒 Scanning frontend image ($(FRONTEND_IMG):$(VERSION))..."
	trivy image --severity HIGH,CRITICAL --exit-code 0 $(FRONTEND_IMG):$(VERSION)
