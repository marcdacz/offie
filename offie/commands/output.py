from __future__ import annotations

from datetime import datetime

from offie.core.context import Context
from offie.core.models import Step

from .registry import BaseCommand, command

LOG_LEVELS = ("debug", "info", "warning", "error")


def _should_log(message_level: str, min_level: str) -> bool:
    """True if message_level is at or above min_level in severity."""
    ml = (message_level or "info").strip().lower()
    mn = (min_level or "info").strip().lower()
    try:
        return LOG_LEVELS.index(ml) >= LOG_LEVELS.index(mn)
    except ValueError:
        return LOG_LEVELS.index("info") >= LOG_LEVELS.index(mn)


def log(
    message_level: str,
    message: str,
    min_level: str,
    prefix: str = "",
) -> None:
    """
    Print a single log line when message_level is at or above min_level.

    Line format: {ISO8601 timestamp} {UPPERCASE_LEVEL} {prefix}{message}
    """
    if not _should_log(message_level, min_level):
        return
    ml = (message_level or "info").strip().lower()
    if ml not in LOG_LEVELS:
        ml = "info"
    level_upper = ml.upper()
    ts = datetime.now().isoformat()
    line = f"{ts} {level_upper} {prefix}{message}"
    print(line)


@command
class PrintCommand(BaseCommand):
    name = "print"
    required_args: list[str] = []

    def validate(self, step: Step) -> list[str]:
        if "value" not in step.args and "message" not in step.args:
            return ["print command requires either 'value' or 'message'"]
        return []

    def execute(self, step: Step, context: Context, executor) -> None:  # type: ignore[override]
        raw = step.args.get("message", step.args.get("value"))
        rendered = context.render_template(raw)
        print(rendered)


@command
class LogCommand(BaseCommand):
    name = "log"
    required_args = ["message"]
    optional_args = ["level"]

    def validate(self, step: Step) -> list[str]:
        errors: list[str] = []
        if "message" not in step.args:
            errors.append("log command requires 'message'")
        level = step.args.get("level")
        if level is not None and str(level).strip().lower() not in LOG_LEVELS:
            errors.append(f"log command 'level' must be one of: {', '.join(LOG_LEVELS)}")
        return errors

    def execute(self, step: Step, context: Context, executor) -> None:  # type: ignore[override]
        raw_message = step.args["message"]
        message = (
            context.render_template(raw_message)
            if isinstance(raw_message, str)
            else str(raw_message)
        )
        level = step.args.get("level") or "info"
        level = str(level).strip().lower()
        if level not in LOG_LEVELS:
            level = "info"
        min_level = getattr(context, "log_level", "info")
        log(level, message, min_level, prefix="")
