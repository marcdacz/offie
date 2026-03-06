from __future__ import annotations

from pathlib import Path

import pytest

from offie.cli import main


def run_workflow__should_complete_successfully__when_inline_workflow_is_executed(
    tmp_path: Path,
) -> None:
    yaml_content = """
workflow:
  name: End To End
  description: Simple end-to-end inline workflow.
  parameters:
    - who: Person to greet
  steps:
    - print: "Hello, {{who}}!"
"""
    path = tmp_path / "workflow.yml"
    path.write_text(yaml_content, encoding="utf-8")

    exit_code = main([str(path), "-p", "who=Offie"])

    assert exit_code == 0


def run_workflow__should_fail_fast__when_workflow_contains_unknown_command(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    yaml_content = """
workflow:
  name: Invalid End To End
  description: Uses an unknown command to trigger validation failure.
  steps:
    - unknown_command: true
"""
    path = tmp_path / "invalid_workflow.yml"
    path.write_text(yaml_content, encoding="utf-8")

    exit_code = main([str(path)])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Workflow validation failed:" in captured.err
    assert "Unknown command 'unknown_command'" in captured.err

