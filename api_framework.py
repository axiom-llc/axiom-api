import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional, Dict, Any


class APIClient:
    """
    Reusable base client for REST API integrations.

    Features:
    - Automatic retries with exponential backoff (5xx, 429, connectivity errors)
    - Rate limiting (requests per second)
    - Configurable timeouts and headers
    - Context manager support
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        requests_per_second: int = 10,
        timeout: int = 30,
        max_retries: int = 5,
        backoff_factor: float = 0.5,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.requests_per_second = requests_per_second
        self._last_call = 0

        self.session = requests.Session()

        headers = {"User-Agent": "Axiom-API-Framework/1.0"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self.session.headers.update(headers)

        # allowed_methods replaces method_whitelist in urllib3 2.0+
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _rate_limit(self):
        """Token-bucket style rate limiting."""
        now = time.time()
        elapsed = now - self._last_call
        min_interval = 1.0 / self.requests_per_second
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self._last_call = time.time()

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        self._rate_limit()
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault("timeout", self.timeout)
        return self.session.request(method.upper(), url, **kwargs)

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[Any, Any]:
        r = self._request("GET", endpoint, params=params)
        r.raise_for_status()
        return r.json()

    def post(self, endpoint: str, data: Optional[Dict] = None, json: Optional[Dict] = None) -> Dict[Any, Any]:
        r = self._request("POST", endpoint, data=data, json=json)
        r.raise_for_status()
        return r.json()

    def put(self, endpoint: str, data: Optional[Dict] = None, json: Optional[Dict] = None) -> Dict[Any, Any]:
        r = self._request("PUT", endpoint, data=data, json=json)
        r.raise_for_status()
        return r.json()

    def delete(self, endpoint: str) -> None:
        r = self._request("DELETE", endpoint)
        r.raise_for_status()

    def close(self):
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
