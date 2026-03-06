from __future__ import annotations

from dataclasses import dataclass

from offie.commands.registry import BaseCommand, registry

from .models import Step, Workflow


@dataclass
class ValidationError:
    location: str
    message: str


def validate_workflow(workflow: Workflow) -> list[ValidationError]:
    """
    Validate that the workflow only uses known commands and that each
    command receives the required arguments.
    """

    errors: list[ValidationError] = []

    _validate_steps(workflow.steps, "steps", errors)

    return errors


def _validate_steps(steps: list[Step], prefix: str, errors: list[ValidationError]) -> None:
    for index, step in enumerate(steps):
        location = f"{prefix}[{index}]"

        command_cls = registry.get(step.command)
        if command_cls is None:
            errors.append(
                ValidationError(
                    location=location,
                    message=f"Unknown command '{step.command}'",
                )
            )
            # Unknown command, no further validation possible for this step.
            continue

        command: BaseCommand = command_cls()
        for msg in command.validate(step):
            errors.append(ValidationError(location=location, message=msg))

        # Recurse into any nested step lists.
        for key, value in step.args.items():
            if isinstance(value, list) and value and isinstance(value[0], Step):
                _validate_steps(value, f"{location}.{key}", errors)
