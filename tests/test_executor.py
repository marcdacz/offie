from __future__ import annotations

from pathlib import Path

import pytest

from offie.core.executor import Executor
from offie.core.models import Parameter, Step, Workflow


def execute_workflow__should_run_all_steps__when_simple_set_and_print_steps_are_defined(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    workflow = Workflow(
        name="executor-simple",
        description=None,
        parameters=[],
        steps=[
            Step(command="set_variable", args={"value": "World", "as": "name"}),
            Step(command="print", args={"value": "Hello, {{name}}!"}),
        ],
        source_path=tmp_path / "inline.yml",
    )

    executor = Executor()
    executor.execute(workflow)

    captured = capsys.readouterr()
    assert "Hello, World!" in captured.out


def execute_workflow__should_apply_cli_overrides__when_parameters_have_defaults(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    workflow = Workflow(
        name="executor-params",
        description=None,
        parameters=[
            Parameter(name="who", description=None, required=False, default="World"),
        ],
        steps=[
            Step(command="print", args={"value": "Hello, {{who}}!"}),
        ],
        source_path=tmp_path / "inline.yml",
    )

    executor = Executor()
    executor.execute(workflow, cli_parameters={"who": "Offie"})

    captured = capsys.readouterr()
    assert "Hello, Offie!" in captured.out


def execute_step__should_raise_runtime_error__when_command_is_unknown(tmp_path: Path) -> None:
    workflow = Workflow(
        name="executor-unknown-command",
        description=None,
        parameters=[],
        steps=[Step(command="does_not_exist", args={})],
        source_path=tmp_path / "inline.yml",
    )

    executor = Executor()

    with pytest.raises(RuntimeError) as excinfo:
        executor.execute(workflow)

    assert "Unknown command 'does_not_exist'" in str(excinfo.value)

