import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:30080';

export const options = {
  stages: [
    { duration: '10s', target: 50 },
    { duration: '30s', target: 100 },
    { duration: '60s', target: 150 },
    { duration: '30s', target: 50 },
    { duration: '10s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],
    http_req_failed: ['rate<0.2'],
  },
};

export default function () {
  // Heavy load: just hit /api/books repeatedly with no sleep
  const res = http.get(`${BASE_URL}/api/books`);
  check(res, {
    'status is 200': (r) => r.status === 200,
  });

  // Also hit /healthz to generate probe traffic
  if (__VU % 10 === 0) {
    http.get(`${BASE_URL}/healthz`);
  }

  // Minimal think time to maximize QPS
  sleep(0.05); // 50ms
}
