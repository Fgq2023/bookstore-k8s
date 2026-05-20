# Cloud-Native Bookstore Demo Video Script

**Project:** DSAA4040 Engineering Track | Group 5  
**Title:** Cloud-Native Online Bookstore on Kubernetes  
**Target Duration:** 3 minutes 30 seconds  
**Resolution:** 1920x1080 (16:9)  
**Style:** Professional, clean, tech-forward with smooth transitions

---

## Video Structure Overview

| Act | Scene | Duration | Focus |
|-----|-------|----------|-------|
| 1. Hook | S01-S03 | 20s | Problem + Solution introduction |
| 2. Features | S04-S09 | 90s | Core user journey (browse → pay) |
| 3. Tech Deep-Dive | S10-S14 | 60s | K8s, HPA, Monitoring, Cache |
| 4. Quality | S15-S16 | 30s | CI/CD + Testing |
| 5. Closing | S17 | 20s | Summary + Group info |

**Total: ~220 seconds (3m 40s)**

---

## Scene-by-Scene Script

### ACT 1: HOOK (0:00 - 0:20)

---

#### **S01 — Opening Title Card**
- **Duration:** 5s
- **Visual:**
  - Dark gradient background (#1a1a2e → #16213e)
  - Animated Kubernetes logo (subtle rotation)
  - Title text fades in: **"Cloud-Native Online Bookstore"**
  - Subtitle: **"Built on Kubernetes | DSAA4040 Group 5"**
  - Bottom: Date "May 2026"
- **Narration:** *[No narration — let music breathe]*
- **Audio:** Upbeat, modern tech intro music (synthwave/corporate)
- **Transition:** Fade to next scene

---

#### **S02 — The Problem**
- **Duration:** 7s
- **Visual:**
  - Split screen or montage:
    - Left: Cluttered monolithic app diagram (messy arrows)
    - Right: Text bullet points fading in:
      - "❌ Scaling issues"
      - "❌ Manual deployments"
      - "❌ No observability"
      - "❌ Security vulnerabilities"
  - Color: Red/orange accents for "problem" feel
- **Narration:**
  > "Traditional web applications struggle with scaling, deployment complexity, and lack of observability. How do we build a modern, production-ready e-commerce system?"
- **Transition:** Quick cut/zoom to solution

---

#### **S03 — The Solution**
- **Duration:** 8s
- **Visual:**
  - Clean architecture diagram (the one from README)
  - Components highlight sequentially:
    1. Ingress glows
    2. Frontend (Vue + nginx) glows
    3. Backend (Flask + Gunicorn) glows
    4. PostgreSQL, Redis, Prometheus glows
  - Center text: **"Cloud-Native Architecture on Kubernetes"**
  - Color: Blue/cyan accents for "solution" feel
- **Narration:**
  > "Our answer: a cloud-native online bookstore. Containerized, orchestrated by Kubernetes, with full observability, auto-scaling, and enterprise-grade security."
- **Transition:** Fade to browser window

---

### ACT 2: CORE FEATURES (0:20 - 1:50)

---

#### **S04 — Landing Page & Browse**
- **Duration:** 15s
- **Visual:**
  - Screen recording: Browser at `http://bookstore.local`
  - Clean bookstore homepage loads
  - Show book grid: "Clean Code", "Design Patterns", etc.
  - Cursor movement (smooth, not jerky)
  - Highlight: Book cards with cover, title, author, price, stock
- **Narration:**
  > "Welcome to our bookstore. Users can browse the complete catalog with real-time stock information. The frontend is a Vue 3 single-page application, served by nginx."
- **On-screen text:** "Vue 3 + Vite + Tailwind CSS"
- **Transition:** Smooth scroll or cut

---

#### **S05 — Search Feature**
- **Duration:** 12s
- **Visual:**
  - Cursor clicks search box
  - Types: "Clean" (with typing effect or speed-up)
  - Results filter in real-time: only "Clean Code" remains
  - Clear search, show "Design Patterns" returns
  - Show empty state: type "XYZ" → "No books found"
- **Narration:**
  > "The search feature queries by title or author instantly, with backend API pagination and Redis caching for sub-millisecond response times."
- **On-screen text:** "Redis Cache + PostgreSQL Indexes"
- **Transition:** Cut to book detail

---

#### **S06 — Book Detail & Add to Cart**
- **Duration:** 15s
- **Visual:**
  - Click on "Clean Code" book card
  - Detail page: ISBN, price $42.99, stock 10
  - Click "Add to Cart" button
  - Toast notification: "Added to cart!" (top-right)
  - Cart badge in navbar updates: 0 → 1
  - Add another copy (quantity: 2)
- **Narration:**
  > "Each book shows detailed information including ISBN and real-time stock. Adding to cart triggers an API call with session isolation. The cart count updates reactively across the entire application."
- **On-screen text:** "Session Isolation + Reactive State"
- **Transition:** Click cart icon

---

#### **S07 — Shopping Cart**
- **Duration:** 15s
- **Visual:**
  - Cart page loads
  - Show item: Clean Code, 2x, $85.98 total
  - Demonstrate quantity update: click + to 3 → total updates
  - Show "Remove" button hover/click → item removed → empty state
  - Re-add item for continuity
- **Narration:**
  > "The shopping cart supports quantity updates and item removal with instant total calculation. Every cart operation is protected against IDOR attacks — users can only modify their own cart items."
- **On-screen text:** "IDOR Protection via JOIN Verification"
- **Transition:** Click "Place Order"

---

#### **S08 — Order Placement (ACID Transaction)**
- **Duration:** 18s
- **Visual:**
  - "Place Order" button click
  - Loading spinner (1s)
  - Redirect to Orders page
  - New order appears: Order #501, Status: "Confirmed"
  - Click order to show details
  - Show status_history JSONB in admin view (optional terminal split)
- **Narration:**
  > "Order placement is wrapped in an ACID database transaction: create order, deduct stock, clear cart, and invalidate the Redis cache — all succeed or all rollback. The order state machine tracks every transition in a JSONB audit trail."
- **On-screen text:** "ACID Transaction + State Machine"
- **Transition:** Cut to payment

---

#### **S09 — Payment & Order Completion**
- **Duration:** 15s
- **Visual:**
  - Click "Pay Now" on order
  - Mock payment modal/overlay
  - "Processing..." → "Payment Successful!"
  - Order status updates: Confirmed → Shipped
  - Return to book list: stock decreased from 10 to 8
- **Narration:**
  > "Our payment mock simulates a gateway, transitioning orders from confirmed to shipped. Stock is atomically deducted, and the cache is invalidated so all users see updated inventory immediately."
- **On-screen text:** "Write-Through Cache Invalidation"
- **Transition:** Fade to terminal/K8s view

---

### ACT 3: TECHNICAL DEEP-DIVE (1:50 - 2:50)

---

#### **S10 — Kubernetes Architecture**
- **Duration:** 12s
- **Visual:**
  - Terminal window: `kubectl get pods -n bookstore`
  - Show running pods:
    - `bookstore-frontend-xxx` (Running)
    - `bookstore-backend-xxx` (2 replicas)
    - `postgres-xxx` (Running)
    - `redis-xxx` (Running)
  - Switch to: `kubectl get svc -n bookstore`
  - Show Services: frontend (NodePort), backend (ClusterIP), postgres, redis
- **Narration:**
  > "Under the hood, everything runs on Kubernetes. We have four core services: frontend, backend, PostgreSQL, and Redis, each isolated by NetworkPolicy for zero-trust security."
- **On-screen text:** "Kustomize + NetworkPolicy"
- **Transition:** Split screen

---

#### **S11 — Horizontal Pod Autoscaler (HPA)**
- **Duration:** 15s
- **Visual:**
  - Left: `kubectl get hpa -n bookstore` (shows target/current CPU)
  - Right: `watch kubectl get pods -n bookstore` (real-time)
  - Run k6 load test (terminal): `make load-test`
  - Watch backend pods scale: 2 → 3 → 4 → 5 replicas
  - Show HPA events: `kubectl describe hpa bookstore-backend -n bookstore`
- **Narration:**
  > "When traffic spikes, the Horizontal Pod Autoscaler scales the backend from two to five replicas based on CPU utilization. We verified this with k6 load testing at 150 virtual users."
- **On-screen text:** "HPA: 2→5 Replicas | CPU Target: 70%"
- **Transition:** Cut to Grafana

---

#### **S12 — Monitoring & Alerting**
- **Duration:** 20s
- **Visual:**
  - Browser: Grafana dashboard at `localhost:3000`
  - Show 6-panel dashboard:
    1. HTTP Request Rate (graph)
    2. Request Duration P95 (graph)
    3. DB Connection Success/Failed (counters)
    4. **DB Pool Used/Free connections** (gauge)
    5. Orders Created (counter)
    6. Cart Items Added (counter)
  - Switch to Prometheus: `http_requests_total` query
  - Show Alertmanager rules YAML (code view):
    - HighLatency, HighErrorRate, DBPoolExhausted...
- **Narration:**
  > "Observability is built-in. Prometheus scrapes metrics every 15 seconds. Grafana dashboards show real-time performance, including database connection pool utilization. Alertmanager watches for five critical conditions — from high latency to pool exhaustion."
- **On-screen text:** "Prometheus + Grafana + Alertmanager"
- **Transition:** Terminal view

---

#### **S13 — Redis Cache in Action**
- **Duration:** 12s
- **Visual:**
  - Terminal: `kubectl exec -it redis-xxx -- redis-cli monitor`
  - Show GET/SET commands flowing
  - Split screen: 
    - Left: `curl http://bookstore.local/api/books` (1st call — slow)
    - Right: Same curl again (2nd call — instant, from cache)
  - Show cache key: `books_list:1:20`
- **Narration:**
  > "Redis serves as our distributed cache. Book listings are cached for 60 seconds. On a cache hit, response time drops from milliseconds to microseconds. If Redis fails, the system gracefully falls back to in-memory caching."
- **On-screen text:** "Redis Primary → Memory Fallback"
- **Transition:** Cut to code/CI

---

#### **S14 — Security Features**
- **Duration:** 10s
- **Visual:**
  - Quick montage of security features:
    - `curl -I` showing security headers (X-Content-Type-Options, HSTS)
    - JWT token in Network tab (browser DevTools)
    - Rate limit test: `curl` loop hitting 429 Too Many Requests
    - `kubectl describe networkpolicy` output
  - Badge icons: 🔒 JWT, 🛡️ Rate Limit, 🔥 NetworkPolicy
- **Narration:**
  > "Security is layered: JWT authentication, Redis-backed rate limiting, zero-trust NetworkPolicies, and non-root containers with dropped capabilities."
- **On-screen text:** "Defense in Depth"
- **Transition:** Fade to GitHub

---

### ACT 4: QUALITY & CI/CD (2:50 - 3:20)

---

#### **S15 — CI/CD Pipeline**
- **Duration:** 15s
- **Visual:**
  - GitHub Actions page showing green workflow run
  - Stages highlight sequentially (scroll or animation):
    1. ✅ Lint (Hadolint + kubeconform)
    2. ✅ Test Backend Unit (75 tests)
    3. ✅ Test Frontend Unit (25 tests)
    4. ✅ Build (Docker Buildx)
    5. ✅ Security Scan (Trivy)
    6. ✅ Deploy Check (Kustomize)
  - Final badge: **"All checks passed"**
- **Narration:**
  > "Every pull request triggers an eight-stage CI pipeline: linting, unit tests, integration tests, frontend E2E with Playwright, Docker builds, Trivy security scans, and Kubernetes manifest validation."
- **On-screen text:** "GitHub Actions | 115 Tests | 90% Coverage"
- **Transition:** Cut to test output

---

#### **S16 — Testing Pyramid**
- **Duration:** 15s
- **Visual:**
  - Pyramid diagram:
    - Top (small): 3 Playwright E2E tests (browser)
    - Middle: 6 Integration tests (testcontainers)
    - Bottom (large): 75 Unit tests (pytest)
  - Show terminal: `pytest tests/ -v` output scrolling
  - Coverage report: 90% in green
  - Frontend tests: `vitest run` + `playwright test` output
- **Narration:**
  > "Our testing strategy follows the pyramid: 75 fast unit tests, 6 integration tests with real PostgreSQL via testcontainers, and 3 Playwright browser tests covering the complete user journey."
- **On-screen text:** "115 Tests | 90% Backend Coverage"
- **Transition:** Fade to closing

---

### ACT 5: CLOSING (3:20 - 3:40)

---

#### **S17 — Closing Card**
- **Duration:** 20s
- **Visual:**
  - Return to architecture diagram (S03), but all components glowing green
  - Summary text fades in:
    - "✅ Cloud-Native on Kubernetes"
    - "✅ Auto-scaling & Self-healing"
    - "✅ Full Observability"
    - "✅ Enterprise Security"
    - "✅ 115 Automated Tests"
  - Final screen:
    - **"Cloud-Native Bookstore"**
    - **"DSAA4040 | Group 5"**
    - Date: May 2026
    - GitHub repo URL (if public)
- **Narration:**
  > "This is our cloud-native bookstore — built for scale, observed in real-time, secured by design, and validated by comprehensive testing. Thank you for watching."
- **Audio:** Music swells, fades out
- **Final frame:** Hold 5 seconds with group member names (optional)

---

## Technical Notes

### Recording Tools Recommended

| Task | Tool | Notes |
|------|------|-------|
| Screen Recording | OBS Studio or QuickTime | 1920x1080, 30fps |
| Terminal Recording | asciinema + svg-term | Or direct terminal capture |
| Browser Automation | Playwright | For consistent, repeatable UI shots |
| Video Editing | DaVinci Resolve (free) or CapCut | Add transitions, text overlays |
| Audio Narration | Audacity + USB mic | Or Mac built-in mic with noise removal |
| Background Music | Pixabay Music or Uppbeat.io | Corporate/tech genre, instrumental |

### Key Recording Tips

1. **Browser Windows**: Use Chrome with minimal bookmarks, hide bookmarks bar, maximize window to 1920x1080
2. **Terminal**: Use dark theme (Dracula or Monokai), increase font size (14-16pt), show only relevant output
3. **Cursor**: Make cursor visible and larger (macOS: Accessibility → Pointer size)
4. **Timing**: Pause 1-2 seconds after each action before cutting — gives viewers time to process
5. **Text Overlays**: Use consistent font (Inter or Roboto), white text with dark semi-transparent background
6. **Zoom**: Use smooth zoom for important details (OBS plugin or post-production)

### Pre-Recording Checklist

- [ ] Minikube cluster is running (`minikube status`)
- [ ] All pods are Ready (`kubectl get pods -n bookstore`)
- [ ] Application is accessible (`curl http://bookstore.local/api/healthz`)
- [ ] Grafana is accessible (if showing dashboards)
- [ ] Terminal windows are sized and themed
- [ ] Browser cache is cleared (for clean first-load shots)
- [ ] Book data is seeded (run demo script if needed)
- [ ] k6 load test script is ready (for HPA scene)
- [ ] Recording software tested (audio levels, resolution)

### One-Take Setup Script

```bash
# Start fresh
make clean
make deploy-tag VERSION=demo

# Wait for all pods
kubectl wait --for=condition=ready pod -l app=bookstore-backend -n bookstore --timeout=120s
kubectl wait --for=condition=ready pod -l app=bookstore-frontend -n bookstore --timeout=120s

# Seed data (if needed)
# curl -X POST http://bookstore.local/api/admin/seed

# Verify endpoints
curl -s http://bookstore.local/api/books | head -c 200
curl -s http://bookstore.local/api/healthz

# Start port-forwards for Grafana (in separate terminal)
make port-forward-grafana &
make port-forward-prometheus &
```

---

## Alternative: Automated Video Generation

If you want to generate this video programmatically, use the `demo-output/` directory:

```bash
# 1. Generate scene screenshots with Playwright
python3 demo-output/build.sh

# 2. Record narration (or use edge-tts)
# 3. Composite with ffmpeg
```

See `demo-output/scenes/` for HTML scene templates and `demo-output/build.sh` for the full pipeline.

---

## Narration Audio File Map

| Scene | File | Duration | Text |
|-------|------|----------|------|
| S02 | `narration/s02.txt` | 7s | "Traditional web applications struggle..." |
| S03 | `narration/s03.txt` | 8s | "Our answer: a cloud-native online bookstore..." |
| S04 | `narration/s04.txt` | 15s | "Welcome to our bookstore..." |
| S05 | `narration/s05.txt` | 12s | "The search feature queries by title..." |
| S06 | `narration/s06.txt` | 15s | "Each book shows detailed information..." |
| S07 | `narration/s07.txt` | 15s | "The shopping cart supports quantity updates..." |
| S08 | `narration/s08.txt` | 18s | "Order placement is wrapped in an ACID..." |
| S09 | `narration/s09.txt` | 15s | "Our payment mock simulates a gateway..." |
| S10 | `narration/s10.txt` | 12s | "Under the hood, everything runs on Kubernetes..." |
| S11 | `narration/s11.txt` | 15s | "When traffic spikes, the Horizontal Pod Autoscaler..." |
| S12 | `narration/s12.txt` | 20s | "Observability is built-in. Prometheus scrapes..." |
| S13 | `narration/s13.txt` | 12s | "Redis serves as our distributed cache..." |
| S14 | `narration/s14.txt` | 10s | "Security is layered: JWT authentication..." |
| S15 | `narration/s15.txt` | 15s | "Every pull request triggers an eight-stage..." |
| S16 | `narration/s16.txt` | 15s | "Our testing strategy follows the pyramid..." |
| S17 | `narration/s17.txt` | 20s | "This is our cloud-native bookstore..." |

**Total narration time: ~234 seconds (~4 minutes)**  
*Note: Adjust pacing in editing to match visual timing (target 3:30 total)*

---

*Script generated on May 20, 2026*
