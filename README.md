# api-integration-framework

Drop `api_framework.py` into any Python project to get production-grade HTTP
behaviour — automatic retry, exponential backoff, and rate limiting — without
rewriting the same error-handling logic for every new integration.

![CI](https://github.com/axiom-llc/api-integration-framework/actions/workflows/ci.yml/badge.svg)

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
- **Extensible** — subclass `APIClient` and override `_auth_headers()` to add
  Bearer tokens, OAuth, HMAC signatures, or any custom scheme
- **Minimal** — one runtime dependency (`requests`); no frameworks, no magic

---

## Installation

```bash
pip install requests
```

Copy `api_framework.py` into your project. No package installation required.

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

See `example_usage.py` for a runnable demo against JSONPlaceholder — no API
key required.

---

## Auth Patterns

The base client sends `api_key` as a query parameter. Override
`_auth_headers()` to use any other scheme:

```python
class BearerClient(APIClient):
    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"}

class HMACClient(APIClient):
    def _auth_headers(self) -> dict:
        signature = hmac.new(self.api_key.encode(), digestmod="sha256").hexdigest()
        return {"X-Signature": signature}
```

Override `_default_headers()` to inject static headers (User-Agent, Content-Type, etc.)
on every request.

---

## Included Examples

**`example_usage.py`** — basic GET / POST against JSONPlaceholder. No key required.

```bash
python example_usage.py
```

**`gemini_client.py`** — production Gemini API client with structured JSON output.
Requires `pip install google-genai` in addition to `requests`.

```bash
export GEMINI_API_KEY=your-key
python gemini_client.py "explain the CAP theorem in 3 bullet points"
```

A working client for any new API takes under 30 minutes from scratch.

---

## Tests

```bash
pytest tests/ -q
```

All tests mock outbound HTTP. No network access or API keys required. CI runs on Python 3.11 and 3.12 on every push.

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

Subclass `APIClient` for any new integration:

```python
class StripeClient(APIClient):
    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"}

    def list_customers(self, limit: int = 10) -> dict:
        return self.get("/v1/customers", params={"limit": limit})

    def create_charge(self, amount: int, currency: str, source: str) -> dict:
        return self.post("/v1/charges", json={
            "amount": amount,
            "currency": currency,
            "source": source,
        })
```

Add pagination, logging, or response validation in the subclass without
touching the retry or session logic.

---

## License

MIT — [Axiom LLC](https://axiom-llc.github.io)
