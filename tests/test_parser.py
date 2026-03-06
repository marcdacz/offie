from __future__ import annotations

from pathlib import Path

import pytest

from offie.core.parser import WorkflowParseError, load_workflow


def load_workflow__should_return_parsed_model__when_inline_minimal_workflow_is_loaded(
    tmp_path: Path,
) -> None:
    yaml_content = """
workflow:
  name: Inline Workflow
  description: Simple inline workflow for parser tests.
  parameters:
    - param1: First parameter
  steps:
    - set_variable:
        value: 123
      as: number
    - print: "Value is {{number}}"
"""
    path = tmp_path / "workflow.yml"
    path.write_text(yaml_content, encoding="utf-8")

    workflow = load_workflow(path)

    assert workflow.name == "Inline Workflow"
    assert workflow.description == "Simple inline workflow for parser tests."
    assert len(workflow.parameters) == 1
    assert workflow.parameters[0].name == "param1"
    assert len(workflow.steps) == 2
    assert workflow.source_path == path


def load_workflow__should_raise_validation_error__when_top_level_workflow_key_is_missing(
    tmp_path: Path,
) -> None:
    yaml_content = """
not_workflow:
  name: Missing top level workflow key
"""
    path = tmp_path / "invalid.yml"
    path.write_text(yaml_content, encoding="utf-8")

    with pytest.raises(WorkflowParseError) as excinfo:
        load_workflow(path)

    assert "Top-level key 'workflow' is required" in str(excinfo.value)


def load_workflow__should_raise_validation_error__when_workflow_section_is_not_mapping(
    tmp_path: Path,
) -> None:
    yaml_content = """
workflow: []
"""
    path = tmp_path / "invalid.yml"
    path.write_text(yaml_content, encoding="utf-8")

    with pytest.raises(WorkflowParseError) as excinfo:
        load_workflow(path)

    assert "The 'workflow' section must be a mapping" in str(excinfo.value)


def load_workflow__should_handle_empty_parameters_and_steps__when_sections_are_missing(
    tmp_path: Path,
) -> None:
    yaml_content = """
workflow:
  name: No Params Or Steps
"""
    path = tmp_path / "no_sections.yml"
    path.write_text(yaml_content, encoding="utf-8")

    workflow = load_workflow(path)

    assert workflow.name == "No Params Or Steps"
    assert workflow.parameters == []
    assert workflow.steps == []


def load_workflow__should_raise_validation_error__when_parameters_section_is_not_list(
    tmp_path: Path,
) -> None:
    yaml_content = """
workflow:
  name: Invalid Params
  parameters:
    not_a_list: true
"""
    path = tmp_path / "invalid_params.yml"
    path.write_text(yaml_content, encoding="utf-8")

    with pytest.raises(WorkflowParseError) as excinfo:
        load_workflow(path)

    assert "workflow.parameters must be a list" in str(excinfo.value)


def load_workflow__should_raise_validation_error__when_steps_section_is_not_list(
    tmp_path: Path,
) -> None:
    yaml_content = """
workflow:
  name: Invalid Steps
  steps:
    not_a_list: true
"""
    path = tmp_path / "invalid_steps.yml"
    path.write_text(yaml_content, encoding="utf-8")

    with pytest.raises(WorkflowParseError) as excinfo:
        load_workflow(path)

    assert "workflow.steps must be a list" in str(excinfo.value)

