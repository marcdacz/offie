from __future__ import annotations

import re
from pathlib import Path

import pytest
from offie.commands.output import (
    log,
)
from offie.core.executor import Executor
from offie.core.models import Step, Workflow
from offie.core.validator import validate_workflow

# ---------------------------------------------------------------------------
# Log util: level gating
# ---------------------------------------------------------------------------


def log__should_print_message__when_message_level_is_at_or_above_min_level(
    capsys: pytest.CaptureFixture[str],
) -> None:
    log("info", "Hello info", "info", prefix="")
    captured = capsys.readouterr()
    assert "Hello info" in captured.out
    assert "INFO" in captured.out


def log__should_print_message__when_min_level_is_debug_and_message_is_debug(
    capsys: pytest.CaptureFixture[str],
) -> None:
    log("debug", "Debug message", "debug", prefix="")
    captured = capsys.readouterr()
    assert "Debug message" in captured.out
    assert "DEBUG" in captured.out


def log__should_not_print__when_message_level_below_min_level(
    capsys: pytest.CaptureFixture[str],
) -> None:
    log("debug", "Should not appear", "info", prefix="")
    captured = capsys.readouterr()
    assert "Should not appear" not in captured.out

    log("info", "Also not", "error", prefix="")
    captured = capsys.readouterr()
    assert "Also not" not in captured.out


# ---------------------------------------------------------------------------
# Log util: format (timestamp + uppercase level)
# ---------------------------------------------------------------------------


def log__should_emit_line_with_iso_timestamp_and_uppercase_level(
    capsys: pytest.CaptureFixture[str],
) -> None:
    log("warning", "Test warning", "debug", prefix="")
    captured = capsys.readouterr()
    line = captured.out.strip()
    # ISO 8601-like: digits, T, digits, optional fractional part
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?", line), line
    assert " WARNING " in line or line.endswith(" WARNING Test warning")
    assert "Test warning" in line


def log__should_include_prefix_when_given(
    capsys: pytest.CaptureFixture[str],
) -> None:
    log("info", "Message", "info", prefix="[Cursor] ")
    captured = capsys.readouterr()
    assert "[Cursor] Message" in captured.out
    assert "INFO" in captured.out


# ---------------------------------------------------------------------------
# LogCommand validation
# ---------------------------------------------------------------------------


def validate_workflow__should_accept_step__when_log_has_message() -> None:
    workflow = Workflow(
        name="log-workflow",
        description=None,
        parameters=[],
        steps=[
            Step(command="log", args={"message": "Starting"}),
        ],
        source_path=None,
    )
    errors = validate_workflow(workflow)
    assert errors == []


def validate_workflow__should_accept_step__when_log_has_message_and_valid_level() -> None:
    workflow = Workflow(
        name="log-workflow",
        description=None,
        parameters=[],
        steps=[
            Step(command="log", args={"message": "OK", "level": "debug"}),
        ],
        source_path=None,
    )
    errors = validate_workflow(workflow)
    assert errors == []


def validate_workflow__should_reject_step__when_log_missing_message() -> None:
    workflow = Workflow(
        name="log-workflow",
        description=None,
        parameters=[],
        steps=[
            Step(command="log", args={"level": "info"}),
        ],
        source_path=None,
    )
    errors = validate_workflow(workflow)
    messages = [e.message for e in errors]
    assert any("log" in m and "message" in m for m in messages)


# ---------------------------------------------------------------------------
# LogCommand execute (via executor, level gating)
# ---------------------------------------------------------------------------


def execute_workflow__should_show_log_message__when_log_level_is_debug(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    workflow = Workflow(
        name="log-debug",
        description=None,
        parameters=[],
        steps=[
            Step(
                command="log",
                args={"message": "Debug visible", "level": "debug"},
            ),
        ],
        source_path=tmp_path / "inline.yml",
    )
    executor = Executor()
    executor.execute(workflow, log_level="debug")
    captured = capsys.readouterr()
    assert "Debug visible" in captured.out
    assert "DEBUG" in captured.out


def execute_workflow__should_not_show_debug_log__when_log_level_is_info(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    workflow = Workflow(
        name="log-info",
        description=None,
        parameters=[],
        steps=[
            Step(
                command="log",
                args={"message": "Debug hidden", "level": "debug"},
            ),
        ],
        source_path=tmp_path / "inline.yml",
    )
    executor = Executor()
    executor.execute(workflow, log_level="info")
    captured = capsys.readouterr()
    assert "Debug hidden" not in captured.out


def execute_workflow__should_show_info_log__when_log_level_is_info(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    workflow = Workflow(
        name="log-info-visible",
        description=None,
        parameters=[],
        steps=[
            Step(
                command="log",
                args={"message": "Info visible", "level": "info"},
            ),
        ],
        source_path=tmp_path / "inline.yml",
    )
    executor = Executor()
    executor.execute(workflow, log_level="info")
    captured = capsys.readouterr()
    assert "Info visible" in captured.out
    assert "INFO" in captured.out
