from __future__ import annotations

import json
from typing import Any

import httpx

from offie.commands.output import log as output_log
from offie.handlers.ai.base import BaseAIHandler, ai_handler

DEFAULT_BASE_URL = "http://localhost:11434"
GENERATE_PATH = "/api/generate"

# Ollama API option keys we forward from workflow options into the request.
OLLAMA_OPTION_KEYS = frozenset(
    {
        "num_ctx",
        "num_predict",
        "temperature",
        "top_p",
        "top_k",
        "repeat_penalty",
        "seed",
        "stop",
        "num_thread",
        "num_gpu",
    }
)
LOG_LEVELS = ("debug", "info", "warning", "error")


@ai_handler
class OllamaHandler(BaseAIHandler):
    """
    AI handler that calls the local Ollama API.
    """

    name = "ollama"
    default_model = "qwen3:4b"

    def __init__(self, base_url: str = DEFAULT_BASE_URL) -> None:
        self._base_url = base_url.rstrip("/")

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        options: dict[str, Any] | None = None,
        log_level: str = "info",
    ) -> str:
        output_log("debug", "Validating options...", log_level, prefix="[Ollama] ")
        opts = options or {}
        effective_model = opts.get("model") or self.default_model
        if not effective_model:
            msg = "No model specified and OllamaHandler has no default_model"
            raise ValueError(msg)

        output_log("debug", "Building request (prompt + system)...", log_level, prefix="[Ollama] ")
        payload: dict[str, object] = {
            "model": effective_model,
            "prompt": prompt,
            "stream": True,
        }
        if system_prompt:
            payload["system"] = system_prompt
        ollama_options = {k: opts[k] for k in OLLAMA_OPTION_KEYS if k in opts}
        if ollama_options:
            payload["options"] = ollama_options

        url = f"{self._base_url}{GENERATE_PATH}"
        output_log("debug", "Calling Ollama (streaming)...", log_level, prefix="[Ollama] ")
        try:
            with httpx.Client(timeout=60.0) as client:
                with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    text = self._consume_stream(response, log_level)
        except httpx.ConnectError as exc:
            msg = (
                "Failed to connect to Ollama at "
                f"{self._base_url}. Is Ollama running? Error: {exc}"
            )
            raise RuntimeError(msg) from exc
        except httpx.HTTPStatusError as exc:
            msg = f"Ollama API error: {exc.response.status_code} - {exc.response.text}"
            raise RuntimeError(msg) from exc

        return text

    def _consume_stream(self, response: httpx.Response, log_level: str) -> str:
        """Read NDJSON stream from Ollama; stream text chunks; return response text."""
        response_chunks: list[str] = []
        stream_started = False
        active_channel: str | None = None
        output_log("info", "Message 1/1:...", log_level, prefix="[Ollama] ")
        for line in response.iter_lines():
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            thinking_part = data.get("thinking")
            if thinking_part is not None:
                thinking_str = str(thinking_part)
                if thinking_str.strip():
                    stream_started, active_channel = self._stream_chunk(
                        text=thinking_str,
                        channel="thinking",
                        log_level=log_level,
                        stream_started=stream_started,
                        active_channel=active_channel,
                    )

            response_part = data.get("response")
            if response_part is not None:
                response_str = str(response_part)
                response_chunks.append(response_str)
                if response_str.strip():
                    stream_started, active_channel = self._stream_chunk(
                        text=response_str,
                        channel="response",
                        log_level=log_level,
                        stream_started=stream_started,
                        active_channel=active_channel,
                    )
            if data.get("done"):
                break

        if stream_started:
            print(flush=True)

        return "".join(response_chunks)

    def _stream_chunk(
        self,
        text: str,
        channel: str,
        log_level: str,
        stream_started: bool,
        active_channel: str | None,
    ) -> tuple[bool, str | None]:
        """Print stream chunks inline to avoid one timestamped line per token."""
        if not self._should_emit_info(log_level):
            return stream_started, active_channel

        next_channel = channel
        if active_channel != channel:
            if stream_started:
                print(flush=True)
            label = "[thinking] " if channel == "thinking" else ""
            print(f"[Ollama] {label}", end="", flush=True)
        print(text, end="", flush=True)
        return True, next_channel

    def _should_emit_info(self, log_level: str) -> bool:
        current_level = (log_level or "info").strip().lower()
        if current_level not in LOG_LEVELS:
            current_level = "info"
        return LOG_LEVELS.index("info") >= LOG_LEVELS.index(current_level)
