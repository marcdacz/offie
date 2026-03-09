from __future__ import annotations

import os
import time
from typing import Any

import httpx  # type: ignore[import-not-found]

from offie.commands.output import log as output_log
from offie.handlers.ai.base import BaseAIHandler, ai_handler

API_BASE = "https://api.cursor.com"
LAUNCH_PATH = "/v0/agents"
POLL_INTERVAL = 5
POLL_TIMEOUT = 300

LOG_LEVELS = ("debug", "info", "warning", "error")


def _should_emit_info(log_level: str) -> bool:
    """True if log_level allows INFO-level output (info or debug)."""
    current = (log_level or "info").strip().lower()
    if current not in LOG_LEVELS:
        current = "info"
    return LOG_LEVELS.index("info") >= LOG_LEVELS.index(current)


def _validate_api_key() -> str:
    """Ensure CURSOR_API_KEY is set; return it."""
    api_key = os.environ.get("CURSOR_API_KEY")
    if not api_key or not api_key.strip():
        msg = "CURSOR_API_KEY is not set. Set it in the environment or in a .env file."
        raise RuntimeError(msg)
    return api_key.strip()


def _validate_options(options: dict[str, Any] | None) -> tuple[str, str, str | None]:
    """Validate options and return (source_repository, model, ref)."""
    opts = options or {}
    source_repository = opts.get("source_repository")
    if not source_repository or not str(source_repository).strip():
        msg = "Cursor handler requires options.source_repository (GitHub repo URL)."
        raise RuntimeError(msg)
    model = str(opts.get("model") or "default")
    ref = opts.get("ref")
    if ref is not None:
        ref = str(ref)
    return (str(source_repository).strip(), model, ref)


def _build_request_body(
    prompt: str,
    system_prompt: str | None,
    source_repository: str,
    model: str,
    ref: str | None,
) -> dict[str, Any]:
    """Build the JSON body for the launch request."""
    prompt_text = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
    body: dict[str, Any] = {
        "prompt": {"text": prompt_text},
        "model": model,
        "source": {"repository": source_repository},
    }
    if ref is not None:
        body["source"]["ref"] = ref
    return body


def _launch_agent(
    client: httpx.Client,
    body: dict[str, Any],
    auth: tuple[str, str],
) -> str:
    """POST to launch the agent; return agent_id."""
    r = client.post(
        f"{API_BASE}{LAUNCH_PATH}",
        json=body,
        auth=auth,
    )
    r.raise_for_status()
    data = r.json()
    agent_id = data.get("id")
    if not agent_id:
        msg = "Cursor API response missing 'id'"
        raise RuntimeError(msg)
    return str(agent_id)


def _extract_assistant_texts(conv: dict[str, Any]) -> list[str]:
    """From a conversation response, return list of assistant message texts."""
    messages = conv.get("messages") or []
    return [m["text"] for m in messages if m.get("type") == "assistant_message" and m.get("text")]


def _fetch_and_print_new_messages(
    client: httpx.Client,
    agent_id: str,
    auth: tuple[str, str],
    printed_count: int,
    previous_texts: list[str],
    log_level: str = "info",
) -> tuple[list[str], int]:
    """
    Fetch conversation; print any new assistant messages when log_level allows INFO;
    return (all_texts, new_printed_count). On fetch failure, returns
    (previous_texts, printed_count) unchanged.
    """
    try:
        r = client.get(
            f"{API_BASE}{LAUNCH_PATH}/{agent_id}/conversation",
            auth=auth,
        )
        r.raise_for_status()
        conv = r.json()
        assistant_texts = _extract_assistant_texts(conv)
        for i in range(printed_count, len(assistant_texts)):
            text = assistant_texts[i]
            if _should_emit_info(log_level):
                output_log(
                    "info",
                    f"Message {i + 1}/{len(assistant_texts)}:\n{text}\n",
                    log_level,
                    prefix="[Cursor] ",
                )
            printed_count += 1
        return (assistant_texts, printed_count)
    except (httpx.ConnectError, httpx.HTTPStatusError):
        return (previous_texts, printed_count)


def _poll_until_finished(
    client: httpx.Client,
    agent_id: str,
    auth: tuple[str, str],
    log_level: str = "info",
) -> list[str]:
    """Poll agent status and conversation; stream new messages when log_level allows INFO;
    return final assistant_texts."""
    deadline = time.monotonic() + POLL_TIMEOUT
    printed_count = 0
    assistant_texts: list[str] = []

    while time.monotonic() < deadline:
        r = client.get(
            f"{API_BASE}{LAUNCH_PATH}/{agent_id}",
            auth=auth,
        )
        r.raise_for_status()
        status_data = r.json()
        status = status_data.get("status")

        assistant_texts, printed_count = _fetch_and_print_new_messages(
            client, agent_id, auth, printed_count, assistant_texts, log_level
        )

        if status == "FINISHED":
            return assistant_texts
        if status == "FAILED":
            msg = f"Cursor agent failed: {status_data}"
            raise RuntimeError(msg)

        time.sleep(POLL_INTERVAL)

    msg = f"Cursor agent did not finish within {POLL_TIMEOUT}s"
    raise RuntimeError(msg)


@ai_handler
class CursorHandler(BaseAIHandler):
    """
    AI handler that uses the Cursor Cloud Agents API.
    Requires CURSOR_API_KEY in the environment (or in .env).
    """

    name = "cursor"
    default_model = "default"

    def __init__(self) -> None:
        self.extra_metadata: dict[str, Any] = {}

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        options: dict[str, Any] | None = None,
        log_level: str = "info",
    ) -> str:
        output_log("debug", "Validating API key...", log_level, prefix="[Cursor] ")
        api_key = _validate_api_key()
        auth = (api_key, "")

        output_log("debug", "Validating options...", log_level, prefix="[Cursor] ")
        source_repository, model, ref = _validate_options(options)

        output_log("debug", "Building request (prompt + source)...", log_level, prefix="[Cursor] ")
        body = _build_request_body(prompt, system_prompt, source_repository, model, ref)

        output_log("debug", "Launching agent...", log_level, prefix="[Cursor] ")
        with httpx.Client(timeout=60.0) as client:
            try:
                agent_id = _launch_agent(client, body, auth)
            except httpx.ConnectError as exc:
                msg = f"Failed to connect to Cursor API: {exc}"
                raise RuntimeError(msg) from exc
            except httpx.HTTPStatusError as exc:
                msg = f"Cursor API error: {exc.response.status_code} - {exc.response.text}"
                raise RuntimeError(msg) from exc

        output_log(
            "debug", "Polling agent status and streaming messages...", log_level, prefix="[Cursor] "
        )
        with httpx.Client(timeout=30.0) as client:
            try:
                assistant_texts = _poll_until_finished(client, agent_id, auth, log_level)
            except (httpx.ConnectError, httpx.HTTPStatusError) as exc:
                msg = f"Cursor API poll error: {exc}"
                raise RuntimeError(msg) from exc

        if assistant_texts:
            return assistant_texts[-1]
        return "{}"
