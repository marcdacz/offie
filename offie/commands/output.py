from __future__ import annotations

from offie.core.context import Context
from offie.core.models import Step

from .registry import BaseCommand, command


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
