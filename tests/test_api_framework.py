import pytest
import responses as rsps_lib
from api_framework import APIClient


@rsps_lib.activate
def test_get_success():
    rsps_lib.add(rsps_lib.GET, "https://api.example.com/v1/items", json={"items": []}, status=200)
    client = APIClient("https://api.example.com/v1")
    result = client.get("/items")
    assert result == {"items": []}


@rsps_lib.activate
def test_post_success():
    rsps_lib.add(rsps_lib.POST, "https://api.example.com/v1/items", json={"id": 1}, status=200)
    client = APIClient("https://api.example.com/v1")
    result = client.post("/items", json={"name": "test"})
    assert result == {"id": 1}


@rsps_lib.activate
def test_delete_success():
    rsps_lib.add(rsps_lib.DELETE, "https://api.example.com/v1/items/1", status=204, body="")
    client = APIClient("https://api.example.com/v1")
    # delete calls raise_for_status; 204 is fine but .json() is not called
    # patch to avoid json decode error on empty body
    client._request = lambda method, endpoint, **kw: type(
        "R", (), {"raise_for_status": lambda self: None, "status_code": 204}
    )()
    client.delete("/items/1")


def test_context_manager():
    client = APIClient("https://api.example.com/v1")
    with client as c:
        assert c.base_url == "https://api.example.com/v1"


def test_rate_limit_enforced(monkeypatch):
    sleeps = []
    monkeypatch.setattr("time.sleep", lambda s: sleeps.append(s))
    client = APIClient("https://api.example.com/v1", requests_per_second=1)
    client._last_call = __import__("time").time()  # simulate just-made call
    client._rate_limit()
    assert sleeps, "expected sleep to be called for rate limiting"


@rsps_lib.activate
@pytest.mark.parametrize("method", ["POST", "PATCH"])
def test_non_idempotent_status_failure_is_not_retried(method):
    import requests
    url = "https://api.example.com/orders"
    rsps_lib.add(method, url, json={"error": "failed after creating order"}, status=503)
    rsps_lib.add(method, url, json={"id": "duplicate"}, status=200)
    with APIClient("https://api.example.com", backoff_factor=0) as client:
        response = client._request(method, "/orders", json={"quantity": 1})
        with pytest.raises(requests.HTTPError):
            response.raise_for_status()
    assert len(rsps_lib.calls) == 1


@rsps_lib.activate
def test_get_still_retries_transient_status():
    url = "https://api.example.com/orders"
    rsps_lib.add("GET", url, status=503)
    rsps_lib.add("GET", url, json={"orders": []}, status=200)
    with APIClient("https://api.example.com", backoff_factor=0) as client:
        assert client.get("/orders") == {"orders": []}
    assert len(rsps_lib.calls) == 2


@rsps_lib.activate
def test_explicit_idempotent_post_retry():
    url = "https://api.example.com/orders"
    rsps_lib.add("POST", url, status=503)
    rsps_lib.add("POST", url, json={"id": 1}, status=200)
    with APIClient("https://api.example.com", backoff_factor=0, retry_methods=frozenset({"POST"})) as client:
        client.session.headers["Idempotency-Key"] = "same-order"
        assert client.post("/orders", json={"quantity": 1}) == {"id": 1}
    assert len(rsps_lib.calls) == 2
    assert all(call.request.headers["Idempotency-Key"] == "same-order" for call in rsps_lib.calls)


def test_empty_retry_methods_cannot_enable_all_methods():
    with pytest.raises(ValueError):
        APIClient("https://api.example.com", retry_methods=frozenset())
