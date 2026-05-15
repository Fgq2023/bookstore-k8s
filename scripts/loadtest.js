import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const apiLatency = new Trend('api_latency');

const BASE_URL = __ENV.BASE_URL || 'http://localhost:30080';

export const options = {
  stages: [
    { duration: '30s', target: 10 },   // Ramp up to 10 VUs
    { duration: '1m', target: 50 },    // Ramp up to 50 VUs
    { duration: '2m', target: 50 },    // Stay at 50 VUs (trigger HPA)
    { duration: '30s', target: 10 },   // Ramp down
    { duration: '30s', target: 0 },    // Cool down
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000'], // 95% under 1s
    errors: ['rate<0.1'],               // Error rate < 10%
  },
};

// Generate random session ID
function sessionId() {
  return `sess-${Math.random().toString(36).substring(2, 15)}`;
}

export default function () {
  const sess = sessionId();

  // 1. Browse books (60% of requests)
  const booksRes = http.get(`${BASE_URL}/api/books`);
  check(booksRes, {
    'books status is 200': (r) => r.status === 200,
    'books returns data': (r) => r.json('count') > 0,
  });
  errorRate.add(booksRes.status !== 200);
  apiLatency.add(booksRes.timings.duration);

  // 2. Search books (20% of requests)
  if (Math.random() < 0.33) {
    const searchRes = http.get(`${BASE_URL}/api/books/search?q=Cloud`);
    check(searchRes, { 'search status is 200': (r) => r.status === 200 });
    errorRate.add(searchRes.status !== 200);
  }

  // 3. Add to cart (10% of requests)
  if (Math.random() < 0.16) {
    const cartRes = http.post(
      `${BASE_URL}/api/cart`,
      JSON.stringify({
        session_id: sess,
        book_id: String(Math.floor(Math.random() * 5) + 1),
        quantity: Math.floor(Math.random() * 3) + 1,
      }),
      { headers: { 'Content-Type': 'application/json' } }
    );
    check(cartRes, { 'cart add status is 200': (r) => r.status === 200 });
    errorRate.add(cartRes.status !== 200);

    // 4. Place order (5% of requests)
    if (Math.random() < 0.5) {
      const orderRes = http.post(
        `${BASE_URL}/api/orders`,
        JSON.stringify({ session_id: sess }),
        { headers: { 'Content-Type': 'application/json' } }
      );
      check(orderRes, { 'order status is 200': (r) => r.status === 200 });
      errorRate.add(orderRes.status !== 200);
    }
  }

  // 5. Health check (mixed in)
  if (Math.random() < 0.1) {
    const healthRes = http.get(`${BASE_URL}/healthz`);
    check(healthRes, { 'healthz is 200': (r) => r.status === 200 });
  }

  sleep(Math.random() * 2 + 0.5); // 0.5-2.5s think time
}
