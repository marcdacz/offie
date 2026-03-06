from __future__ import annotations

from typing import List

from offie.core.context import Context
from offie.core.models import Step

from .registry import command
from .utils import CommandWithEval


@command
class SetVariableCommand(CommandWithEval):
    name = "set_variable"
    required_args = ["as"]

    def validate(self, step: Step) -> List[str]:
        errors: List[str] = []
        if "as" not in step.args:
            errors.append("set_variable requires an 'as' argument")
        if "value" not in step.args:
            errors.append("set_variable requires a 'value' argument")
        return errors

    def execute(self, step: Step, context: Context, executor) -> None:
        target = step.args["as"]
        raw_value = step.args["value"]
        if isinstance(raw_value, str) and "{{" in raw_value:
            value = self._eval(raw_value, context, executor)
        else:
            value = raw_value
        context.set(target, value)

