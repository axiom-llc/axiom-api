#!/usr/bin/env python3
"""
gemini-client.py — Gemini API client built on APIClient
Demonstrates: framework extension, LLM API integration, production error handling

Requires:
    pip install requests
    export GEMINI_API_KEY=your-key
"""

import os
import sys
import json

# Assumes run from apex root or api-integration-framework is on PYTHONPATH
try:
    from api_framework import APIClient
except ImportError:
    print("api_framework not found — see github.com/axiom-llc/api-integration-framework")
    sys.exit(1)

GEMINI_BASE = "https://generativelanguage.googleapis.com"
GEMINI_MODEL = "gemini-2.5-flash"


class GeminiClient(APIClient):
    """Production Gemini API client with retry, rate limiting, and structured output."""

    def __init__(self, api_key: str = None, requests_per_second: int = 5):
        super().__init__(
            base_url=GEMINI_BASE,
            api_key=api_key or os.environ["GEMINI_API_KEY"],
            requests_per_second=requests_per_second,
            max_retries=5,
            backoff_factor=1.0,
        )
        self.model = GEMINI_MODEL

    def generate(self, prompt: str, system: str = None) -> str:
        """Generate a response. Returns text string."""
        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        body = {"contents": contents}

        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}

        endpoint = f"/v1beta/models/{self.model}:generateContent"
        params = {"key": self._api_key()}

        response = self.post(endpoint, json=body, params=params)
        return response["candidates"][0]["content"]["parts"][0]["text"]

    def generate_json(self, prompt: str, system: str = None) -> dict:
        """Generate and parse a JSON response."""
        json_prompt = f"{prompt}\n\nRespond with valid JSON only. No markdown fences."
        raw = self.generate(json_prompt, system=system)
        clean = raw.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(clean)

    def _api_key(self) -> str:
        return self.session.headers.get("Authorization", "").replace("Bearer ", "")


# ── Demo ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else "Summarise the key principles of clean system design in 3 bullet points."

    with GeminiClient() as client:
        print(f"Model : {client.model}")
        print(f"Prompt: {prompt}\n")

        # Text generation
        response = client.generate(prompt)
        print("Response:\n", response)

        # JSON generation
        json_prompt = "List 3 use cases for AI automation in enterprise workflows. Return as JSON array of objects with 'use_case' and 'impact' fields."
        structured = client.generate_json(json_prompt)
        print("\nStructured output:")
        print(json.dumps(structured, indent=2))
