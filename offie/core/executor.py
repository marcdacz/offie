from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from offie.commands.registry import registry

from .context import Context
from .expressions import ExpressionEvaluator
from .models import Step, Workflow


class Executor:
    """
    Executes a validated Workflow.
    """

    def __init__(self, expression_evaluator: ExpressionEvaluator | None = None) -> None:
        self.expression_evaluator = expression_evaluator or ExpressionEvaluator()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def execute(self, workflow: Workflow, cli_parameters: dict[str, Any] | None = None) -> None:
        """
        Execute the workflow using the provided CLI parameter overrides.
        """

        parameters = cli_parameters or {}
        context = self._build_context(workflow, parameters)
        self.execute_steps(workflow.steps, context)

    def execute_steps(self, steps: Iterable[Step], context: Context) -> None:
        """
        Execute a list of steps in the given context.
        """

        for step in steps:
            self._execute_step(step, context)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _build_context(self, workflow: Workflow, cli_parameters: dict[str, Any]) -> Context:
        """
        Build the initial Context from workflow parameters and CLI overrides.
        """

        context = Context(workflow_name=workflow.name, workflow_file=workflow.source_path or "")

        # Apply workflow parameter defaults, overridden by CLI values.
        defaults: dict[str, Any] = {}
        for param in workflow.parameters:
            if param.default is not None:
                defaults[param.name] = param.default

        merged: dict[str, Any] = {**defaults, **cli_parameters}

        for name, value in merged.items():
            context.set(name, value)

        return context

    def _execute_step(self, step: Step, context: Context) -> None:
        command_cls = registry.get(step.command)
        if command_cls is None:
            msg = f"Unknown command '{step.command}' at execution time"
            raise RuntimeError(msg)

        command = command_cls()
        try:
            command.execute(step, context, self)
        except Exception as exc:  # pragma: no cover - simple error wrapper
            msg = f"Error executing command '{step.command}': {exc}"
            raise RuntimeError(msg) from exc
