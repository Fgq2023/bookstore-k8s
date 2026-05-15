# AGENTS.md — Cloud-Native Bookstore (Kubernetes)

## Project context
- DSAA4040 class project. Target runtime is **Minikube** on Docker.
- No CI, no automated test suite, no real package manager beyond Make + Docker.

## Architecture (3 tiers)
- **Database**: PostgreSQL 15 (Alpine), deployed via `k8s/base/deployment-postgres.yaml`. Uses PVC `postgres-pvc` and Secret `db-credentials`.
- **Backend**: Custom Python 3.11 HTTP server (`src/backend/main.py`, *not* FastAPI/Flask). Entrypoint: `python3 -u main.py`. Port `8000`. Depends on `psycopg2-binary`. Falls back to an in-memory book list if PostgreSQL is unreachable. Calls `init_database()` on startup to create schema and seed sample data.
- **Frontend**: Static HTML (`src/frontend/index.html`) served by nginx 1.25-alpine. Port `80`. Not a real Node/Vite app; `package.json` and `vite.config.js` are placeholders.

## Developer commands
- Start Minikube:
  ```bash
  minikube start --driver=docker --cpus=2 --memory=4096
  minikube addons enable ingress metrics-server
  ```
- Build & deploy (local images):
  ```bash
  make load deploy
  ```
  > `make load` uses `minikube image load` to transfer host-built images into the Minikube node. This avoids the shell-isolation bug of the old `eval $(minikube docker-env)` approach.
- Verify:
  ```bash
  make test                 # pod status + rollout status
  minikube service bookstore-frontend --url
  ```
- Clean:
  ```bash
  make clean                # kubectl delete -k k8s/overlays/minikube
  ```
- Security scan (requires [Trivy](https://aquasecurity.github.io/trivy/)):
  ```bash
  make scan
  ```

## Kubernetes specifics
- Manifests are **Kustomize**-based. Overlay: `k8s/overlays/minikube/`. Base: `k8s/base/`.
- Namespace is `bookstore`.
- `imagePullPolicy: Never` is set for backend and frontend. Images **must** exist inside the Minikube node’s container runtime.
- Ingress manifest is included in the base resources and patched to `bookstore.local` in the overlay. To use it, add `bookstore.local` to `/etc/hosts` pointing to the Minikube IP.
  - **Ingress gotcha fixed**: Removed `nginx.ingress.kubernetes.io/rewrite-target: /` annotation from `ingress.yaml`. The rewrite was stripping `/api` prefix, causing backend 404 for `/api/books`. Frontend nginx's `try_files` already handles SPA routing, so no rewrite is needed.
- Frontend Service is `NodePort` on `30080`. Backend Service is `ClusterIP` (port `80` → targetPort `8000`).
- **Updating images**: Since `imagePullPolicy: Never` is used, after rebuilding images you must restart the deployment for pods to pick up the new image:
  ```bash
  kubectl rollout restart deployment/bookstore-backend -n bookstore
  kubectl rollout restart deployment/bookstore-frontend -n bookstore
  ```
- NetworkPolicy zero-trust mesh: `networkpolicy-db.yaml` (DB←backend), `networkpolicy-frontend.yaml` (Ingress→frontend→backend only), `networkpolicy-backend.yaml` (frontend→backend→DB only). **Minikube caveat**: the default bridge CNI does not enforce NetworkPolicy. To test/verify policies, start Minikube with `--cni=calico` (or another CNI that supports NetworkPolicy).

## Backend gotchas
- **Environment variables**: `main.py` reads `DB_HOST`, `DB_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`. It also reads `APP_ENV` (default: `development`) and `LOG_LEVEL` (default: `info`). It does **not** read `DATABASE_URL`.
- **Deployment now injects DB credentials from Secret**: `deployment-backend.yaml` uses `valueFrom.secretKeyRef` to inject `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` from the `db-credentials` Secret. `main.py` no longer contains hardcoded credentials; if environment variables are absent, it falls back to in-memory mode automatically.
- API endpoints:
  - `GET /healthz` — liveness probe (returns DB connectivity status)
  - `GET /ready` — readiness probe (returns `"ready"` or `"ready (fallback)"` with HTTP 200; never returns 503 to avoid K8s removing the pod from endpoints during temporary DB downtime)
  - `GET /api/books`
  - `GET /api/books/<id>`
  - `GET /api/books/search?q=<keyword>`
  - `POST /api/cart` — add item to cart (`session_id`, `book_id`, `quantity`)
  - `GET /api/cart?session_id=xxx` — view cart
  - `PUT /api/cart/item/<id>` — update quantity (0 = delete)
  - `DELETE /api/cart/item/<id>` — remove item
  - `POST /api/orders` — place order from cart
  - `GET /api/orders?session_id=xxx` — list orders
  - `GET /api/orders/<id>` — order details
- **JSON serialization**: `DecimalEncoder` handles `Decimal` (from PostgreSQL `NUMERIC`) and `datetime` (from `TIMESTAMP`). If you add new column types, extend the encoder.
- `log_message` is overridden to suppress default HTTP request logs.

## Frontend gotchas
- The only build step for the frontend image is `COPY index.html /usr/share/nginx/html/index.html` in the Dockerfile. Do not run `npm run build` expecting a real build.
- `nginx.conf` defines a synthetic `/healthz` endpoint returning JSON. It **also proxies `/api/`** to the backend service (`bookstore-backend:80`), so the SPA works correctly through both Ingress and NodePort.
- Because nginx proxies `/api/`, the `fetch('/api/books')` call works when accessed through Ingress (`bookstore.local`) **or** directly via NodePort (`:30080`).
- Container runs as UID `101` (`nginx` user). The Dockerfile pre-creates and `chown`s `/var/cache/nginx`, `/var/log/nginx`, and `/var/run/nginx.pid` to avoid permission errors.

## Advanced features
- **HPA (Horizontal Pod Autoscaler)**: `k8s/base/hpa.yaml` defines autoscaling for backend (min 2, max 5, target CPU 70%, memory 80%) and frontend (min 1, max 3, target CPU 70%). Requires `minikube addons enable metrics-server`. Verified with k6 load test: backend scales 2→5 under 150 VUs.
- **Prometheus-style metrics**: Backend exposes `GET /metrics` returning counters for `http_requests_total`, `http_request_duration_seconds`, `db_connections_success_total`, `db_connections_failed_total`, `orders_created_total`, `cart_items_added_total`. Scraped by kube-prometheus-stack via ServiceMonitor.
- **Grafana Dashboard**: `k8s/base/grafana-dashboard.yaml` provisions a 4-panel dashboard (HTTP rate, latency, DB connections, business metrics). Deploy to `monitoring` namespace via `make deploy-monitoring`.
- **CI/CD**: `.github/workflows/ci.yml` runs lint (Hadolint, kubeconform), build (Docker Buildx), security scan (Trivy SARIF → GitHub Security tab), and Kustomize build check on every push/PR.
- **Security scan**: `make scan` runs Trivy against local images. CI runs the same scan on every build. Trivy is configured with `exit-code: 0` and `ignore-unfixed: true` for CRITICAL/HIGH severity: vulnerabilities are reported to the GitHub Security tab but do not fail the build. This is a pragmatic choice for a course project; in production, use `exit-code: 1` to block builds with patchable CVEs.
- **Database Schema v2**: Alembic migration `002` adds `updated_at` (auto-updating triggers), `stock_quantity` to books, `status_history` JSONB to orders, and `CHECK` constraint for order statuses (`pending`, `confirmed`, `shipped`, `delivered`, `cancelled`).
- **Inventory Management**: Orders check stock before creation and atomically deduct quantities. Returns 400 if stock is insufficient.
- **Order State Machine**: Orders are created with `status='pending'`, then transition to `confirmed` after stock deduction. Full `status_history` audit trail is persisted.
- **JSON Structured Logging**: Backend uses `python-json-logger` in production mode (`APP_ENV=production`) for structured logs compatible with Loki/ELK.

## Verification / demo
- `scripts/demo-final.sh` performs end-to-end validation: pod status, metrics, inventory/state-machine, HPA scaling, security policies.
- `scripts/loadtest.js` (k6): full shopping flow simulation with thresholds.
- `scripts/loadtest-hpa.js` (k6): high-intensity load to trigger HPA scaling.
- `make load-test`: runs k6 via Docker against the Minikube NodePort.
- `make port-forward-prometheus` / `make port-forward-grafana`: quick access to observability UIs.

## Security conventions
- All containers run as non-root with dropped capabilities (`drop: ["ALL"]`).
- `runAsUser` values: backend `1000`, frontend `101`, postgres `70`.
- **NetworkPolicy** isolates traffic: frontend only accepts from Ingress Controller and egresses to backend; backend only accepts from frontend and egresses to DB; DB only accepts from backend.
- **HEALTHCHECK** is present in both backend (`/ready`) and frontend (`/healthz`) Dockerfiles for runtime health monitoring.
- **Base image patching**: Both Dockerfiles run `apt-get upgrade` (backend) / `apk upgrade` (frontend) during build to patch known system vulnerabilities before deployment.
