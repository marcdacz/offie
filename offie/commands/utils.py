from __future__ import annotations

from typing import Any, TYPE_CHECKING

from offie.core.context import Context
from offie.core.expressions import ExpressionEvaluator

from .registry import BaseCommand

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from offie.core.executor import Executor


class CommandWithEval(BaseCommand):
    """
    Base class for commands that need expression evaluation.
    """

    def _eval(self, expression: str, context: Context, executor: "Executor") -> Any:
        evaluator: ExpressionEvaluator = executor.expression_evaluator
        return evaluator.evaluate(expression, context)

