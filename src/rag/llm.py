"""Ollama chat API client using only the Python standard library."""

import json
from urllib.error import URLError
from urllib.request import Request, urlopen


class OllamaClient:
    def __init__(self, base_url: str, model: str, timeout: int = 120) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def generate(self, prompt: str, system: str) -> str:
        body = json.dumps({
            "model": self.model,
            "stream": False,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        }).encode("utf-8")
        request = Request(f"{self.base_url}/api/chat", data=body, headers={"Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except URLError as exc:
            raise ConnectionError(f"Cannot reach Ollama at {self.base_url}. Start Ollama and pull '{self.model}'.") from exc
        except TimeoutError as exc:
            raise ConnectionError("Ollama request timed out") from exc
        return payload["message"]["content"].strip()