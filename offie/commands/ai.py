from __future__ import annotations

import copy
import json
import re
import time
from typing import Any

from offie.core.context import Context
from offie.core.models import Step
from offie.handlers.ai import (
    cursor,  # noqa: F401
    ollama,  # noqa: F401
)

# Import handlers so they register with the AI registry when this command is loaded.
from offie.handlers.ai import registry as ai_registry  # noqa: F401

from .registry import BaseCommand, command

_SYSTEM_PROMPT_JSON_ONLY = (
    "You must respond ONLY with valid JSON. No markdown, no code fences, no text before or after.\n"
    "Your entire response must be directly parseable by JSON.parse() / json.loads().\n"
    "Use double quotes for strings. Do not use trailing commas."
)

_FENCE_RE = re.compile(r"```(?:json)?\s*\n(.*?)\n\s*```", re.DOTALL)


def _extract_json(text: str) -> str | None:
    """Try to extract a JSON object from text that may contain markdown fences or prose.

    Returns the extracted JSON string on success, or None if nothing valid is found.
    """
    # 1. Try fenced code blocks (last match first — most likely the final answer).
    for match in reversed(_FENCE_RE.findall(text)):
        candidate = match.strip()
        try:
            obj = json.loads(candidate)
            if isinstance(obj, dict):
                return candidate
        except json.JSONDecodeError:
            continue

    # 2. Try the outermost { … } span.
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            obj = json.loads(candidate)
            if isinstance(obj, dict):
                return candidate
        except json.JSONDecodeError:
            pass

    return None


def _resolve_options_templates(value: Any, context: Context) -> Any:
    """Recursively resolve {{var}} in string values of dicts/lists."""
    if isinstance(value, str):
        return context.render_template(value)
    if isinstance(value, dict):
        return {k: _resolve_options_templates(v, context) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_options_templates(v, context) for v in value]
    return value


@command
class CallAIAgentCommand(BaseCommand):
    name = "call_ai_agent"
    required_args = ["handler", "prompt", "as"]
    optional_args = ["model", "options"]

    def validate(self, step: Step) -> list[str]:
        errors: list[str] = []
        for arg in self.required_args:
            if arg not in step.args:
                errors.append(f"call_ai_agent requires '{arg}'")
        return errors

    def execute(self, step: Step, context: Context, executor: Any) -> None:
        handler_name = step.args["handler"]
        prompt = step.args["prompt"]
        as_var = step.args["as"]

        options = copy.deepcopy(step.args.get("options") or {})
        if step.args.get("model") is not None:
            options["model"] = step.args["model"]
        resolved_options = _resolve_options_templates(options, context)

        resolved_prompt = context.render_template(prompt) if isinstance(prompt, str) else prompt

        handler_cls = ai_registry.get(handler_name)
        if handler_cls is None:
            msg = (
                f"Unknown AI handler '{handler_name}'. Available: {list(ai_registry.all().keys())}"
            )
            raise RuntimeError(msg)

        handler = handler_cls()
        start = time.perf_counter()
        raw_response = handler.generate(
            prompt=str(resolved_prompt),
            system_prompt=_SYSTEM_PROMPT_JSON_ONLY,
            options=resolved_options,
            log_level=getattr(context, "log_level", "info"),
        )
        duration_seconds = time.perf_counter() - start
        execution_duration = f"{duration_seconds:.2f}s"

        metadata: dict[str, Any] = {
            "handler": handler_name,
            "model": resolved_options.get("model") or getattr(handler, "default_model", None),
            "execution_duration": execution_duration,
            "output_files": [],
        }

        # Merge handler-specific extra metadata (e.g. agent_id, agent_summary).
        extra = getattr(handler, "extra_metadata", None)
        if isinstance(extra, dict):
            metadata.update(extra)

        try:
            result = json.loads(raw_response)
            if not isinstance(result, dict):
                result = {"response": raw_response, "__metadata": metadata}
                metadata["parse_error"] = "JSON did not produce a top-level object"
            else:
                result["__metadata"] = metadata
        except json.JSONDecodeError:
            # Attempt to extract JSON from text with markdown fences or prose.
            extracted = _extract_json(raw_response)
            if extracted is not None:
                result = json.loads(extracted)
                result["__metadata"] = metadata
            else:
                result = {
                    "response": raw_response,
                    "__metadata": {**metadata, "parse_error": "No valid JSON found in response"},
                }

        context.set(as_var, result)
