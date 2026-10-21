import http from "k6/http";
import { check, sleep } from "k6";

const BASE_URL = __ENV.K6_BASE_URL || "http://api:8000";

export const options = {
  stages: [
    { duration: "5s", target: 3 },
    { duration: "40s", target: 3 },
    { duration: "5s", target: 0 },
  ],
  thresholds: {
    checks: ["rate>0.99"],
    http_req_duration: ["p(95)<500"],
    http_req_failed: ["rate<0.01"],
  },
};

export function setup() {
  const deadline = Date.now() + 60_000;

  while (Date.now() < deadline) {
    const response = http.get(`${BASE_URL}/healthz`);
    if (response.status === 200) {
      return;
    }
    sleep(1);
  }

  throw new Error(`API did not become healthy at ${BASE_URL}/healthz`);
}

export default function () {
  const includeExpectedNotFound = __ITER % 5 === 0;
  const path = includeExpectedNotFound ? "/items/999999" : "/items";
  const expectedStatus = includeExpectedNotFound ? 404 : 200;
  const response = http.get(`${BASE_URL}${path}`, {
    responseCallback: http.expectedStatuses(200, 404),
  });

  check(response, {
    [`${path} responds with ${expectedStatus}`]: (result) =>
      result.status === expectedStatus,
  });

  sleep(1);
}
