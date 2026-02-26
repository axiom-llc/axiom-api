# api-integration-framework

Reusable Python base client for production-grade REST API integrations.

Built for automation pipelines where reliability is non-negotiable: transient failures retry automatically, rate limits are respected, and errors surface cleanly.

## Features

- **Exponential backoff** — automatic retry on 429/5xx and connectivity errors (up to 5 attempts)
- **Rate limiting** — configurable requests-per-second throttling via token-bucket
- **Context manager** — guaranteed session cleanup with `with` statement
- **Extensible** — subclass `APIClient` to add auth schemes, pagination, or custom error handling
- **Minimal** — one dependency (`requests`)

## Usage

```python
from api_framework import APIClient

with APIClient(
    base_url="https://api.example.com",
    api_key="your-key",
    requests_per_second=10,
) as client:
    data = client.get("/endpoint", params={"key": "value"})
    result = client.post("/endpoint", json={"field": "value"})
```

See `example_usage.py` for a runnable demo against a public test API.

## Examples

- `example_usage.py` — basic GET/POST against JSONPlaceholder (no key required)
- `gemini_client.py` — production Gemini API client with structured JSON output

```bash
export GEMINI_API_KEY=your-key
python gemini_client.py "explain the CAP theorem in 3 bullet points"
```

A working client for any new API takes under 30 minutes from scratch.

## vs. raw requests

| | Raw requests | APIClient |
|---|---|---|
| Transient error handling | Crashes | Auto-retries |
| Rate limiting | Manual / none | Built-in |
| Session cleanup | Manual | Context manager |
| Retry logic | Per-integration | Once, inherited |
| Lines to integrate new API | ~40+ | ~10 |

## Installation

```bash
pip install requests
```

## License

MIT — [Axiom LLC](https://axiom-llc.github.io)
