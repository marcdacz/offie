from __future__ import annotations

from typing import TYPE_CHECKING

from offie.core.context import Context
from offie.core.models import Step

from .registry import command
from .utils import CommandWithEval

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from offie.core.executor import Executor


_DEFAULT_MAX_WHILE_ITERATIONS = 1_000


@command
class IfCommand(CommandWithEval):
    name = "if"
    # Condition is always provided as the primary value.
    required_args = ["value"]

    def validate(self, step: Step) -> list[str]:
        errors: list[str] = []
        if "value" not in step.args:
            errors.append("if requires a condition value")
        if "then" not in step.args:
            errors.append("if requires a 'then' step list")
        return errors

    def execute(self, step: Step, context: Context, executor: Executor) -> None:
        condition = step.args["value"]
        result = bool(self._eval(condition, context, executor))
        branch_key = "then" if result else "else"
        nested = step.args.get(branch_key) or []
        executor.execute_steps(nested, context)


@command
class WhileCommand(CommandWithEval):
    name = "while"
    # Loop condition is always provided as the primary value.
    required_args = ["value", "do"]
    optional_args = ["max_iterations"]

    def validate(self, step: Step) -> list[str]:
        errors: list[str] = []
        if "value" not in step.args:
            errors.append("while requires a condition value")
        if "do" not in step.args:
            errors.append("while requires a 'do' step list")
        return errors

    def execute(self, step: Step, context: Context, executor: Executor) -> None:
        condition = step.args["value"]
        body = step.args.get("do") or []

        max_iterations_expr = step.args.get("max_iterations")
        if max_iterations_expr is None:
            max_iterations = _DEFAULT_MAX_WHILE_ITERATIONS
        else:
            max_iterations = int(self._eval(str(max_iterations_expr), context, executor))

        iterations = 0
        while True:
            if iterations >= max_iterations:
                msg = "while loop exceeded maximum iterations"
                raise RuntimeError(msg)
            if not bool(self._eval(condition, context, executor)):
                break
            executor.execute_steps(body, context)
            iterations += 1


@command
class ForCommand(CommandWithEval):
    name = "for"
    required_args = ["start", "end", "as", "do"]

    def execute(self, step: Step, context: Context, executor: Executor) -> None:
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
class ForEachCommand(CommandWithEval):
    name = "for_each"
    required_args = ["value", "as", "do"]

    def validate(self, step: Step) -> list[str]:
        errors: list[str] = []
        for arg in ("value", "as", "do"):
            if arg not in step.args:
                errors.append(f"for_each requires a '{arg}' argument")
        return errors

    def execute(self, step: Step, context: Context, executor: Executor) -> None:
        items_expr = step.args["value"]
        var_name = step.args["as"]
        body = step.args.get("do") or []

        items = self._eval(str(items_expr), context, executor)
        for item in items:
            context.set(var_name, item)
            executor.execute_steps(body, context)
