from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest  # type: ignore[import]
from offie.core.models import Step, Workflow


@pytest.fixture
def minimal_workflow_yaml() -> str:
    """
    Inline YAML for a minimal but valid workflow definition.
    """

    return """
workflow:
  name: Example Workflow
  description: Simple inline workflow for testing.
  parameters:
    - param1: First parameter
  steps:
    - set_variable:
        value: 42
      as: answer
    - print: "Hello, {{answer}}"
"""


@pytest.fixture
def tmp_workflow_file(tmp_path: Path) -> Path:
    """
    Factory fixture to create workflow files from inline YAML strings.
    """

    def _create(yaml_content: str) -> Path:
        path = tmp_path / "workflow.yml"
        path.write_text(yaml_content, encoding="utf-8")
        return path

    # type: ignore[return-value]
    return _create  # type: ignore[return-value]


@pytest.fixture
def simple_workflow_model() -> Workflow:
    """
    Minimal Workflow model instance useful for executor/validator tests.
    """

    return Workflow(
        name="inline-workflow",
        description="Inline workflow model for tests",
        parameters=[],
        steps=[],
        source_path=None,
    )


@pytest.fixture
def make_step() -> Any:
    """
    Helper to build Step instances for validation and execution tests.
    """

    def _make(command: str, **args: dict[str, Any]) -> Step:
        return Step(command=command, args=dict(args))

    return _make
