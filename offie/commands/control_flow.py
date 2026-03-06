from __future__ import annotations

from typing import Any, List, TYPE_CHECKING

from offie.core.context import Context
from offie.core.expressions import ExpressionEvaluator
from offie.core.models import Step
from .registry import BaseCommand, command


if TYPE_CHECKING:  # pragma: no cover - type checking only
    from offie.core.executor import Executor


_DEFAULT_MAX_WHILE_ITERATIONS = 10_000


class _CommandWithEval(BaseCommand):
    """
    Mixin providing access to the expression evaluator.
    """

    def _eval(self, expression: str, context: Context, executor: "Executor") -> Any:
        evaluator: ExpressionEvaluator = executor.expression_evaluator
        return evaluator.evaluate(expression, context)


@command
class PrintCommand(_CommandWithEval):
    name = "print"
    required_args: List[str] = []

    def validate(self, step: Step) -> List[str]:
        if "value" not in step.args and "message" not in step.args:
            return ["print command requires either 'value' or 'message'"]
        return []

    def execute(self, step: Step, context: Context, executor: "Executor") -> None:
        raw = step.args.get("message", step.args.get("value"))
        rendered = context.render_template(raw)
        print(rendered)


@command
class SetVariableCommand(_CommandWithEval):
    name = "set_variable"
    required_args = ["as"]

    def validate(self, step: Step) -> List[str]:
        errors: List[str] = []
        if "as" not in step.args:
            errors.append("set_variable requires an 'as' argument")
        if "value" not in step.args:
            errors.append("set_variable requires a 'value' argument")
        return errors

    def execute(self, step: Step, context: Context, executor: "Executor") -> None:
        target = step.args["as"]
        raw_value = step.args["value"]
        if isinstance(raw_value, str) and "{{" in raw_value:
            value = self._eval(raw_value, context, executor)
        else:
            value = raw_value
        context.set(target, value)


@command
class IfCommand(_CommandWithEval):
    name = "if"
    # Condition is always provided as the primary value.
    required_args = ["value"]

    def validate(self, step: Step) -> List[str]:
        errors: List[str] = []
        if "value" not in step.args:
            errors.append("if requires a condition value")
        if "then" not in step.args:
            errors.append("if requires a 'then' step list")
        return errors

    def execute(self, step: Step, context: Context, executor: "Executor") -> None:
        condition = step.args["value"]
        result = bool(self._eval(condition, context, executor))
        branch_key = "then" if result else "else"
        nested = step.args.get(branch_key) or []
        executor.execute_steps(nested, context)


@command
class WhileCommand(_CommandWithEval):
    name = "while"
    # Loop condition is always provided as the primary value.
    required_args = ["value", "do"]

    def validate(self, step: Step) -> List[str]:
        errors: List[str] = []
        if "value" not in step.args:
            errors.append("while requires a condition value")
        if "do" not in step.args:
            errors.append("while requires a 'do' step list")
        return errors

    def execute(self, step: Step, context: Context, executor: "Executor") -> None:
        condition = step.args["value"]
        body = step.args.get("do") or []
        iterations = 0
        while True:
            if iterations >= _DEFAULT_MAX_WHILE_ITERATIONS:
                msg = "while loop exceeded maximum iterations"
                raise RuntimeError(msg)
            if not bool(self._eval(condition, context, executor)):
                break
            executor.execute_steps(body, context)
            iterations += 1


@command
class ForCommand(_CommandWithEval):
    name = "for"
    required_args = ["start", "end", "as", "do"]

    def execute(self, step: Step, context: Context, executor: "Executor") -> None:
        start_expr = step.args["start"]
        end_expr = step.args["end"]
        var_name = step.args["as"]
        body = step.args.get("do") or []

        start = int(self._eval(str(start_expr), context, executor))
        end = int(self._eval(str(end_expr), context, executor))

        for index in range(start, end):
            context.set(var_name, index)
            executor.execute_steps(body, context)


@command
class ForEachCommand(_CommandWithEval):
    name = "for_each"
    required_args = ["value", "as", "do"]

    def validate(self, step: Step) -> List[str]:
        errors: List[str] = []
        for arg in ("value", "as", "do"):
            if arg not in step.args:
                errors.append(f"for_each requires a '{arg}' argument")
        return errors

    def execute(self, step: Step, context: Context, executor: "Executor") -> None:
        items_expr = step.args["value"]
        var_name = step.args["as"]
        body = step.args.get("do") or []

        items = self._eval(str(items_expr), context, executor)
        for item in items:
            context.set(var_name, item)
            executor.execute_steps(body, context)

