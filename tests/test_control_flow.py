from __future__ import annotations

from pathlib import Path

from offie.core.context import Context
from offie.core.executor import Executor
from offie.core.models import Step, Workflow


def run_if_command__should_execute_then_branch__when_condition_is_true(
    tmp_path: Path,
) -> None:
    context = Context(workflow_name="if-then", workflow_file=tmp_path / "inline.yml")
    context.set("flag", True)

    workflow = Workflow(
        name="if-then",
        description=None,
        steps=[
            Step(
                command="if",
                args={
                    "value": "{{flag}}",
                    "then": [
                        Step(
                            command="set_variable",
                            args={"value": "then-branch", "as": "result"},
                        )
                    ],
                    "else": [
                        Step(
                            command="set_variable",
                            args={"value": "else-branch", "as": "result"},
                        )
                    ],
                },
            )
        ],
        source_path=tmp_path / "inline.yml",
    )

    executor = Executor()
    executor.execute_steps(workflow.steps, context)

    assert context.get("result") == "then-branch"


def run_if_command__should_execute_else_branch__when_condition_is_false(
    tmp_path: Path,
) -> None:
    context = Context(workflow_name="if-else", workflow_file=tmp_path / "inline.yml")
    context.set("flag", False)

    workflow = Workflow(
        name="if-else",
        description=None,
        steps=[
            Step(
                command="if",
                args={
                    "value": "{{flag}}",
                    "then": [
                        Step(
                            command="set_variable",
                            args={"value": "then-branch", "as": "result"},
                        )
                    ],
                    "else": [
                        Step(
                            command="set_variable",
                            args={"value": "else-branch", "as": "result"},
                        )
                    ],
                },
            )
        ],
        source_path=tmp_path / "inline.yml",
    )

    executor = Executor()
    executor.execute_steps(workflow.steps, context)

    assert context.get("result") == "else-branch"


def run_while_command__should_repeat_body__when_condition_remains_true(
    tmp_path: Path,
) -> None:
    context = Context(workflow_name="while-loop", workflow_file=tmp_path / "inline.yml")
    context.set("i", 0)

    workflow = Workflow(
        name="while-loop",
        description=None,
        steps=[
            Step(
                command="while",
                args={
                    "value": "{{i}} < 3",
                    "do": [
                        Step(
                            command="set_variable",
                            args={"value": "{{i}} + 1", "as": "i"},
                        )
                    ],
                },
            )
        ],
        source_path=tmp_path / "inline.yml",
    )

    executor = Executor()
    executor.execute_steps(workflow.steps, context)

    assert context.get("i") == 3


def run_for_command__should_iterate_over_range__when_start_and_end_are_given(
    tmp_path: Path,
) -> None:
    context = Context(workflow_name="for-loop", workflow_file=tmp_path / "inline.yml")

    workflow = Workflow(
        name="for-loop",
        description=None,
        steps=[
            Step(
                command="for",
                args={
                    "start": "0",
                    "end": "3",
                    "as": "index",
                    "do": [
                        Step(
                            command="set_variable",
                            args={"value": "{{index}}", "as": "last"},
                        )
                    ],
                },
            )
        ],
        source_path=tmp_path / "inline.yml",
    )

    executor = Executor()
    executor.execute_steps(workflow.steps, context)

    assert context.get("last") == 2


def run_for_each_command__should_execute_body_for_each_item__when_iterable_is_list(
    tmp_path: Path,
) -> None:
    context = Context(workflow_name="for-each", workflow_file=tmp_path / "inline.yml")
    context.set("items", [1, 2, 3])

    workflow = Workflow(
        name="for-each",
        description=None,
        steps=[
            Step(
                command="for_each",
                args={
                    "value": "{{items}}",
                    "as": "item",
                    "do": [
                        Step(
                            command="set_variable",
                            args={"value": "{{item}}", "as": "last"},
                        )
                    ],
                },
            )
        ],
        source_path=tmp_path / "inline.yml",
    )

    executor = Executor()
    executor.execute_steps(workflow.steps, context)

    assert context.get("last") == 3
