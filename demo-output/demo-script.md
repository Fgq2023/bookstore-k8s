# Cloud-Native Bookstore Demo Video Script
# DSAA4040 Engineering Track | Group 5
# Target Duration: 7-9 minutes | Resolution: 1920x1080

---

## Video Structure Overview

| Act | Scenes | Duration | Content |
|-----|--------|----------|---------|
| 1. Introduction | S01-S02 | 30s | Title + Project Overview |
| 2. Architecture | S03-S04 | 75s | Three-tier design + Data flow |
| 3. Deployment | S05 | 60s | One-command deployment |
| 4. Core Features | S06-S10 | 120s | Browse → Search → Cart → Order → Pay |
| 5. Auto-scaling | S11-S12 | 70s | HPA trigger + Scale back |
| 6. Resilience | S13-S14 | 55s | Pod failure + Auto-recovery |
| 7. Observability | S15 | 45s | Grafana + Prometheus + Alerts |
| 8. Performance | S16 | 35s | Redis cache latency comparison |
| 9. Quality | S17-S18 | 60s | Test pyramid + Coverage |
| 10. CI/CD | S19 | 30s | GitHub Actions pipeline |
| 11. Security | S20 | 25s | Defense in depth |
| 12. Closing | S21 | 20s | Summary + Credits |

**Total: ~625 seconds (10m 25s)** → Edit down to 7-9 minutes

---

## ACT 1: INTRODUCTION (0:00 - 0:30)

---

### S01 — Opening Title Card
- **Duration:** 10s
- **Visual:** Animated title with Kubernetes logo, project name, group info
- **Narration:** [No narration, just background music]
- **File:** `scenes/s01-title.html`

---

### S02 — Project Overview
- **Duration:** 20s
- **Visual:** Split screen - problem statement left, solution architecture right
- **Narration:**
  > "This is our cloud-native online bookstore, a production-ready e-commerce system built on Kubernetes. We demonstrate modern cloud engineering practices: microservices architecture, automated scaling, comprehensive observability, and enterprise-grade security."
- **File:** Screen recording of app homepage

---

## ACT 2: ARCHITECTURE & DATA FLOW (0:30 - 1:45)

---

### S03 — Three-Tier Architecture
- **Duration:** 40s
- **Visual:** Architecture diagram with components highlighting sequentially
  1. Ingress Controller glows
  2. Frontend (Vue + nginx) glows
  3. Backend (Flask + Gunicorn) glows
  4. PostgreSQL glows
  5. Redis glows
  6. Prometheus + Grafana glows
- **Narration:**
  > "Our system follows a classic three-tier architecture. At the edge, an Ingress Controller routes traffic. The frontend is a Vue 3 single-page application served by nginx. The backend API runs Flask with Gunicorn. Data is persisted in PostgreSQL with Alembic migrations. Redis provides distributed caching. And the entire stack is observable through Prometheus metrics and Grafana dashboards."
- **File:** `scenes/s03-solution.html`

---

### S04 — Request Data Flow
- **Duration:** 35s
- **Visual:** Animated flow diagram showing a user request lifecycle
  1. User → Ingress (highlight path)
  2. Ingress → Frontend Service → Frontend Pod
  3. Frontend Pod → Backend Service → Backend Pod
  4. Backend checks Redis cache (hit/miss animation)
  5. Cache miss → PostgreSQL query
  6. Response flows back with X-Request-ID header
  7. Prometheus scrapes /metrics endpoint
- **Narration:**
  > "When a user sends a request, it enters through the Ingress Controller. The frontend nginx serves the Vue SPA or proxies API calls to the backend. The backend first checks Redis cache. On a hit, it returns in microseconds. On a miss, it queries PostgreSQL and populates the cache. Every response carries an X-Request-ID for distributed tracing, while Prometheus continuously scrapes performance metrics."
- **File:** New HTML animation or terminal recording

---

## ACT 3: ONE-COMMAND DEPLOYMENT (1:45 - 2:45)

---

### S05 — Deployment Walkthrough
- **Duration:** 60s
- **Visual:** Terminal screen recording showing:
  ```bash
  $ minikube start --driver=docker --cpus=2 --memory=4096
  $ minikube addons enable ingress metrics-server
  $ make deploy-tag VERSION=demo
  ```
  - Show docker build output (backend + frontend)
  - Show `minikube image load` progress
  - Show `kubectl apply` creating resources
  - Show pods starting up: `kubectl get pods -w -n bookstore`
  - Show `kubectl wait` for readiness
  - Show `make status` output
  - Show `make test` verifying health checks
- **Narration:**
  > "Deployment is fully automated. A single command, make deploy-tag, orchestrates the entire workflow. It builds Docker images, loads them into Minikube, updates Kustomize image tags, and deploys all Kubernetes resources. Here we see the backend and frontend containers building, images being transferred, and pods initializing with health probes. The initContainer runs database migrations before the application starts. Within two minutes, all services are running and health checks pass."
- **Overlay text:**
  - "Docker Build"
  - "Image Load"
  - "Kustomize Apply"
  - "Health Checks"

---

## ACT 4: CORE FEATURES (2:45 - 4:45)

---

### S06 — Browse Book Catalog
- **Duration:** 25s
- **Visual:** Browser at `http://localhost:8080`
  - Homepage loads with book grid
  - Show 6 books with cover, title, author, price, stock
  - Cursor hovers over book card showing hover effect
- **Narration:**
  > "The bookstore homepage presents the complete catalog with real-time stock quantities. Each book card displays the title, author, ISBN, price, and current availability."

---

### S07 — Search with Pagination
- **Duration:** 20s
- **Visual:**
  - Type "Clean" in search box
  - Results filter instantly
  - Show "No results" for "XYZ"
  - Clear search, show pagination controls at bottom
  - Click page 2
- **Narration:**
  > "Search queries by title or author with instant filtering. The backend API supports pagination with configurable page sizes, returning total counts and metadata."

---

### S08 — Book Detail & Cart
- **Duration:** 25s
- **Visual:**
  - Click on "Clean Code"
  - Detail page: ISBN, price $42.99, stock 10
  - Click "Add to Cart" → Toast notification
  - Cart badge updates: 0 → 1
  - Click "Add to Cart" again → quantity: 2
  - Click Cart icon
- **Narration:**
  > "The detail view shows complete book metadata. Adding to cart triggers a POST request with session isolation. The reactive cart counter updates globally across the application."

---

### S09 — Shopping Cart Operations
- **Duration:** 25s
- **Visual:**
  - Cart page shows "Clean Code", quantity 2, total $85.98
  - Click + to increase to 3 → total updates
  - Click - to decrease to 1 → total updates
  - Click Remove → empty state with "Your cart is empty"
  - Re-add book
- **Narration:**
  > "The cart supports quantity adjustments with real-time total calculation. Every cart operation is protected against IDOR attacks through JOIN-based ownership verification. Users can only modify their own cart items."

---

### S10 — Order Placement & Payment
- **Duration:** 25s
- **Visual:**
  - Click "Place Order"
  - Loading spinner
  - Redirect to Orders page
  - New order: #501, status "Confirmed"
  - Click "Pay Now"
  - "Processing..." → "Payment Successful"
  - Status changes: Confirmed → Shipped
  - Navigate back to homepage, stock decreased from 10 to 8
- **Narration:**
  > "Order placement is wrapped in an ACID transaction: create order, atomically deduct stock, clear the cart, and invalidate the Redis cache — all succeed or all rollback. The payment mock transitions orders through a state machine with full JSONB audit trails. Write-through cache invalidation ensures all users see updated inventory immediately."

---

## ACT 5: AUTO-SCALING (4:45 - 5:55)

---

### S11 — HPA Trigger: Scale Up
- **Duration:** 40s
- **Visual:** Terminal recording
  ```bash
  $ kubectl get hpa -n bookstore
  $ watch kubectl get pods -n bookstore
  # In another terminal:
  $ make load-test
  ```
  - Watch backend replicas: 2 → 3 → 4 → 5
  - HPA shows CPU rising above 70% target
  - kubectl describe hpa shows scaling events
- **Narration:**
  > "Horizontal Pod Autoscaler monitors CPU utilization every 15 seconds. When load increases, it automatically scales the backend from two to five replicas. Here we run a k6 load test with 150 virtual users. Watch the replica count increase as CPU crosses the 70 percent threshold."
- **Overlay:** "k6 Load Test: 150 VUs"

---

### S12 — HPA Recovery: Scale Down
- **Duration:** 30s
- **Visual:** Terminal recording
  - Stop load test
  - Watch pods scale back: 5 → 4 → 3 → 2
  - Show HPA events: "New size: 2; reason: All metrics below target"
- **Narration:**
  > "When load subsides, HPA gracefully scales back down to the minimum replica count. This elastic scaling ensures efficient resource utilization — we only pay for what we need, when we need it."

---

## ACT 6: RESILIENCE & SELF-HEALING (5:55 - 6:50)

---

### S13 — Simulating Pod Failure
- **Duration:** 25s
- **Visual:** Terminal recording
  ```bash
  $ kubectl get pods -n bookstore
  $ kubectl delete pod -n bookstore -l app=bookstore-backend
  $ kubectl get pods -n bookstore -w
  ```
  - Show pod terminating
  - Show new pod created by Deployment
  - Watch new pod progress: Pending → ContainerCreating → Running
- **Narration:**
  > "Kubernetes provides self-healing capabilities. If we manually delete a backend pod, the Deployment controller immediately creates a replacement. The new pod goes through initialization, runs database migrations, and passes health checks before receiving traffic."

---

### S14 — Database Disconnection Recovery
- **Duration:** 30s
- **Visual:** Terminal recording
  ```bash
  $ kubectl scale deployment bookstore-db -n bookstore --replicas=0
  $ curl http://localhost:8080/api/healthz
  # Show fallback mode response
  $ kubectl scale deployment bookstore-db -n bookstore --replicas=1
  $ curl http://localhost:8080/api/healthz
  # Show recovery
  ```
- **Narration:**
  > "Our application gracefully handles database failures. When PostgreSQL becomes unreachable, the backend automatically switches to in-memory fallback mode, serving cached book data without crashing. When the database recovers, connections are re-established seamlessly."

---

## ACT 7: OBSERVABILITY (6:50 - 7:35)

---

### S15 — Monitoring Dashboard
- **Duration:** 45s
- **Visual:** Grafana dashboard (real or `scenes/s12-monitoring.html`)
  - Show 6 panels:
    1. HTTP Request Rate graph
    2. P95 Latency graph
    3. DB Connection Success/Failed counters
    4. DB Pool Used/Free gauge
    5. Orders Created counter
    6. Cart Items Added counter
  - Switch to Prometheus: query `http_requests_total`
  - Show Alertmanager rules: `kubectl get prometheusrules -n monitoring`
- **Narration:**
  > "Observability is built into every layer. Prometheus scrapes metrics every 15 seconds. The Grafana dashboard shows real-time HTTP rates, latency percentiles, database connection pool utilization, and business metrics like orders and cart operations. Alertmanager watches for five critical conditions including high latency, error rates, and pool exhaustion."

---

## ACT 8: PERFORMANCE (7:35 - 8:10)

---

### S16 — Redis Cache Latency Comparison
- **Duration:** 35s
- **Visual:** Terminal recording
  ```bash
  # Cold cache (first request)
  $ time curl -s http://localhost:8080/api/books > /dev/null
  real    0m0.045s

  # Warm cache (second request)
  $ time curl -s http://localhost:8080/api/books > /dev/null
  real    0m0.003s

  # Redis monitor
  $ kubectl exec -it redis-xxx -- redis-cli monitor
  GET books_list:1:20
  ```
- **Narration:**
  > "Redis provides dramatic performance improvements. The first request takes 45 milliseconds as it queries PostgreSQL. Subsequent requests hit the Redis cache and return in 3 milliseconds — a 15x speedup. If Redis fails, the system gracefully falls back to in-memory caching."
- **Overlay:** "Cache Miss: 45ms → Cache Hit: 3ms (15x faster)"

---

## ACT 9: TESTING & QUALITY (8:10 - 9:10)

---

### S17 — Test Pyramid Execution
- **Duration:** 30s
- **Visual:** Terminal recording
  ```bash
  $ make test-backend
  # pytest output scrolling: 75 tests passing
  $ make test-frontend
  # vitest output: 25 tests passing
  $ make test-frontend-e2e
  # playwright output: 3 tests passing
  ```
- **Narration:**
  > "Quality is ensured through a comprehensive testing pyramid: 75 fast unit tests with mocked dependencies, 6 integration tests using real PostgreSQL via testcontainers, and 3 Playwright browser tests covering the complete user journey from login to payment."

---

### S18 — Coverage Report
- **Duration:** 30s
- **Visual:** Terminal recording
  ```bash
  $ cd src/backend && pytest tests/ --cov=. --cov-report=html
  $ ls htmlcov/
  $ python3 -m http.server 8888 --directory htmlcov/
  # Browser: localhost:8888
  ```
  - Show coverage report: 90% overall
  - Click through routes/ (88%), utils/ (92%), schemas.py (95%)
- **Narration:**
  > "Backend test coverage is measured at 90 percent. Every endpoint has both happy-path and error-case tests. The coverage report shows detailed per-module breakdowns, ensuring critical paths are thoroughly validated."

---

## ACT 10: CI/CD PIPELINE (9:10 - 9:40)

---

### S19 — GitHub Actions Workflow
- **Duration:** 30s
- **Visual:** Browser showing GitHub Actions
  - Show workflow diagram with 8 stages
  - Click into each stage:
    1. Lint: Hadolint + kubeconform (green)
    2. Backend Unit Tests: pytest 75 tests (green)
    3. Backend Integration: testcontainers (green, continue-on-error)
    4. Frontend Unit: Vitest 25 tests + build (green)
    5. Frontend E2E: Playwright 3 tests (green, continue-on-error)
    6. Build: Docker Buildx (green)
    7. Security Scan: Trivy SARIF (green)
    8. Deploy Check: Kustomize validate (green)
- **Narration:**
  > "Every pull request triggers an eight-stage CI pipeline. Required jobs include unit tests and build, while integration and browser tests run optionally so external dependencies don't block the pipeline. Security scanning with Trivy uploads vulnerability reports to GitHub Security tab."

---

## ACT 11: SECURITY (9:40 - 10:05)

---

### S20 — Defense in Depth
- **Duration:** 25s
- **Visual:** Terminal + Browser montage
  ```bash
  # Security headers
  $ curl -I http://localhost:8080/api/books
  # Show: X-Content-Type-Options, X-Frame-Options, HSTS

  # Rate limiting
  $ for i in {1..6}; do curl -s http://localhost:8080/api/auth/register; done
  # Show 429 Too Many Requests

  # Network policy
  $ kubectl describe networkpolicy -n bookstore
  ```
- **Narration:**
  > "Security is layered throughout the stack. All responses include security headers. Rate limiting protects authentication endpoints. Zero-trust NetworkPolicies restrict traffic flow. And containers run as non-root with dropped capabilities."

---

## ACT 12: CLOSING (10:05 - 10:25)

---

### S21 — Summary & Credits
- **Duration:** 20s
- **Visual:** `scenes/s17-closing.html` with animated achievements
  - "Cloud-Native on Kubernetes"
  - "Auto-scaling & Self-healing"
  - "Full Observability"
  - "Enterprise Security"
  - "115 Automated Tests"
- **Narration:**
  > "This is our cloud-native bookstore — built for scale, observed in real-time, resilient to failures, secured by design, and validated by comprehensive testing. Thank you for watching."

---

## Production Notes

### Recording Checklist

Before recording:
- [ ] Minikube running with all addons enabled
- [ ] All pods Ready (`kubectl get pods -n bookstore`)
- [ ] Frontend accessible via port-forward or Ingress
- [ ] Grafana accessible (`make port-forward-grafana`)
- [ ] Terminal: Dracula theme, 14pt font, 1920x1080
- [ ] Browser: Chrome maximized, bookmarks hidden
- [ ] Cursor size increased for visibility
- [ ] `scripts/loadtest.js` ready for HPA demo
- [ ] k6 Docker image available

### Recommended Tools

| Task | Tool |
|------|------|
| Screen Recording | OBS Studio (free) |
| Terminal Recording | asciinema or direct terminal capture |
| Browser Automation | Playwright (for consistent screenshots) |
| Video Editing | DaVinci Resolve (free) or CapCut |
| Audio | Audacity + USB mic |
| Music | Pixabay Music (royalty-free) |

### One-Take Setup

```bash
# Start fresh
cd /mnt/d/Class/DSAA4040/bookstore-k8s

# Verify cluster
minikube status
kubectl get pods -n bookstore

# Start port-forwards (run in separate terminals)
kubectl port-forward -n bookstore svc/bookstore-frontend 8080:80
kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 80:80
make port-forward-grafana &

# Verify endpoints
curl http://localhost:8080/api/healthz
curl http://bookstore.local/api/books  # if using Ingress

# Ready to record!
```

---

*Script updated on May 20, 2026*
*Target duration: 7-9 minutes*
*Recommended output: 1080p30, MP4 H.264*
