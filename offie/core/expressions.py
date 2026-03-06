from __future__ import annotations

import re
from typing import Any

from simpleeval import SimpleEval  # type: ignore[import]

from .context import Context


_TEMPLATE_PATTERN = re.compile(r"{{\s*([a-zA-Z_][\w\.]*)\s*}}")


class ExpressionEvaluator:
    """
    Wraps simpleeval to evaluate expressions used in conditions and
    value computations.
    """

    def prepare_expression(self, raw: str) -> str:
        """
        Replace `{{name}}` placeholders in an expression string with bare
        identifiers understood by the evaluator.
        """

        def _replace(match: re.Match[str]) -> str:
            return match.group(1)

        return _TEMPLATE_PATTERN.sub(_replace, raw)

    def evaluate(self, expression: str, context: Context) -> Any:
        """
        Evaluate an expression string using the given context.
        """

        prepared = self.prepare_expression(expression)
        names = context.as_expression_names()
        evaluator = SimpleEval(names=names)
        return evaluator.eval(prepared)

