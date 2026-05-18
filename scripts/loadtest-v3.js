import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('errors');
const apiLatency = new Trend('api_latency');

const BASE_URL = __ENV.BASE_URL || 'http://localhost:30080';

export const options = {
  stages: [
    { duration: '10s', target: 20 },
    { duration: '20s', target: 50 },
    { duration: '10s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000'],
    errors: ['rate<0.1'],
  },
};

function sessionId() {
  return `sess-${Math.random().toString(36).substring(2, 15)}`;
}

export default function () {
  const sess = sessionId();

  // Test pagination
  const page = Math.floor(Math.random() * 3) + 1;
  const booksRes = http.get(`${BASE_URL}/api/books?page=${page}&per_page=2`);
  check(booksRes, {
    'books status is 200': (r) => r.status === 200,
    'books has pagination': (r) => r.json('page') === page,
    'books has total': (r) => r.json('total') > 0,
  });
  errorRate.add(booksRes.status !== 200);
  apiLatency.add(booksRes.timings.duration);

  // Test auth register
  const username = `user_${Math.random().toString(36).substring(2, 8)}`;
  const regRes = http.post(
    `${BASE_URL}/api/auth/register`,
    JSON.stringify({ username, email: `${username}@test.com`, password: 'secret123' }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  check(regRes, {
    'register status is 201 or 409': (r) => r.status === 201 || r.status === 409,
  });
  errorRate.add(regRes.status !== 201 && regRes.status !== 409);

  // Test payment mock (on existing order)
  if (Math.random() < 0.2) {
    const payRes = http.post(
      `${BASE_URL}/api/payments`,
      JSON.stringify({ order_id: 1 }),
      { headers: { 'Content-Type': 'application/json' } }
    );
    check(payRes, {
      'payment returns valid status': (r) => r.status === 200 || r.status === 400,
    });
    errorRate.add(payRes.status !== 200 && payRes.status !== 400);
  }

  // Test security headers
  if (Math.random() < 0.1) {
    const hdrRes = http.get(`${BASE_URL}/api/books`);
    check(hdrRes, {
      'has X-Frame-Options': (r) => r.headers['X-Frame-Options'] === 'DENY',
      'has HSTS': (r) => r.headers['Strict-Transport-Security'] !== undefined,
    });
  }

  sleep(0.5);
}
