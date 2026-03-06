from __future__ import annotations

from offie.core.models import Step, Workflow
from offie.core.validator import ValidationError, validate_workflow


def validate_workflow__should_accept_workflow__when_all_commands_and_arguments_are_valid() -> None:
    workflow = Workflow(
        name="valid-workflow",
        description=None,
        steps=[
            Step(command="set_variable", args={"value": 1, "as": "x"}),
            Step(command="print", args={"value": "Hello"}),
        ],
    )

    errors: list[ValidationError] = validate_workflow(workflow)

    assert errors == []


def validate_workflow__should_reject_workflow__when_command_is_unknown() -> None:
    workflow = Workflow(
        name="invalid-workflow",
        description=None,
        steps=[Step(command="does_not_exist", args={})],
    )

    errors: list[ValidationError] = validate_workflow(workflow)

    assert len(errors) == 1
    assert errors[0].location == "steps[0]"
    assert "Unknown command 'does_not_exist'" in errors[0].message


def validate_workflow__should_collect_errors__when_nested_steps_are_invalid() -> None:
    workflow = Workflow(
        name="nested-invalid",
        description=None,
        steps=[
            Step(
                command="if",
                args={
                    "value": "{{sys.date}} == '2025-01-01'",
                    "then": [
                        Step(command="set_variable", args={"as": "x"}),
                        Step(command="for_each", args={"as": "item", "do": []}),
                    ],
                },
            )
        ],
    )

    errors: list[ValidationError] = validate_workflow(workflow)

    messages = {err.message for err in errors}
    locations = {err.location for err in errors}

    assert "set_variable requires a 'value' argument" in messages
    assert "for_each requires a 'value' argument" in messages
    assert "steps[0].then[0]" in locations
    assert "steps[0].then[1]" in locations
