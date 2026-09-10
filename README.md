# axiom-api

Production-grade HTTP client base for REST API integrations — automatic retries for idempotent methods,
exponential backoff, and rate limiting without rewriting the same error-handling
logic for every new integration.

![CI](https://github.com/axiom-llc/axiom-api/actions/workflows/ci.yml/badge.svg)

Built for automation pipelines where reliability is non-negotiable: transient
failures retry silently, rate limits are respected, sessions are always cleaned
up, and errors surface as typed exceptions rather than silent data corruption.

---

## Features

- **Exponential backoff** — automatic retry on 429 / 5xx and connectivity
  errors, up to 5 attempts with jittered delay
- **Rate limiting** — configurable requests-per-second throttling via interval
  throttle; safe for burst workloads
- **Context manager** — guaranteed session cleanup; no leaked connections under
  error conditions
- **Extensible** — subclass `APIClient` to add Bearer tokens, OAuth, HMAC
  signatures, or any custom auth scheme
- **Minimal** — one runtime dependency (`requests`); no frameworks, no magic

---

## Installation

```bash
git clone https://github.com/axiom-llc/axiom-api
cd axiom-api
pip install -e .
```

---

## Usage

```python
from api_framework import APIClient

with APIClient(
    base_url="https://api.example.com",
    api_key="your-key",
    requests_per_second=10,
) as client:
    data   = client.get("/endpoint", params={"key": "value"})
    result = client.post("/endpoint", json={"field": "value"})
```

---

## Retry safety

Status and read-error retries default to idempotent HTTP methods (GET, HEAD,
OPTIONS, PUT, DELETE, TRACE). POST and PATCH are not retried after a response or
read failure, since the server may already have applied their side effects.
Connection failures before sending a request may still retry. Unclassified
errors are not retried. Set `max_retries=0` to disable all retries.

Only opt in to POST/PATCH retries when the endpoint guarantees idempotency,
for example with a server-supported idempotency key:

```python
with APIClient("https://api.example.com", retry_methods=frozenset({"GET", "POST"})) as client:
    client.session.headers["Idempotency-Key"] = "unique-operation-id"
    client.post("/orders", json={"quantity": 1})
```

## Auth Patterns

The base client sends `api_key` as a Bearer token header. Override in a
subclass to use any other scheme:

```python
class HMACClient(APIClient):
    def _auth_headers(self) -> dict:
        signature = hmac.new(self.api_key.encode(), digestmod="sha256").hexdigest()
        return {"X-Signature": signature}
```

---

## Included Examples

**`gemini_client/`** — production Gemini API client with structured JSON output,
built on `APIClient`.

```bash
export GEMINI_API_KEY=your-key
python -m gemini_client.client "explain the CAP theorem in 3 bullet points"
```

---

## Tests

```bash
pip install -e ".[dev]"
pytest tests/ -q
```

All tests mock outbound HTTP — no network access or API keys required.
CI runs on Python 3.11 and 3.12 on every push.

---

## vs. raw requests

|                            | Raw `requests`  | `APIClient`          |
|----------------------------|-----------------|----------------------|
| Transient error handling   | Crashes         | Auto-retries         |
| Rate limiting              | Manual / none   | Built-in             |
| Session cleanup            | Manual          | Context manager      |
| Retry logic                | Per-integration | Once, inherited      |
| Auth scheme                | Per-integration | Override one method  |
| Lines to integrate new API | ~40+            | ~10                  |

---

## Extending

```python
from api_framework import APIClient

class StripeClient(APIClient):
    def list_customers(self, limit: int = 10) -> dict:
        return self.get("/v1/customers", params={"limit": limit})

    def create_charge(self, amount: int, currency: str, source: str) -> dict:
        return self.post("/v1/charges", json={
            "amount": amount,
            "currency": currency,
            "source": source,
        })
```

---

## License

MIT — [AXIOM LLC](https://axiom-llc.github.io)
