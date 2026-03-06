from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml  # type: ignore[import]

from .models import Parameter, Step, Workflow


_MODIFIER_KEYS = {"as", "do", "condition", "then", "else", "start", "end"}


class WorkflowParseError(Exception):
    pass


def load_workflow(path: str | Path) -> Workflow:
    """
    Load and parse a workflow YAML file into a Workflow model.
    """

    workflow_path = Path(path)
    with workflow_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict) or "workflow" not in data and "worklfow" not in data:
        msg = "Top-level key 'workflow' is required"
        raise WorkflowParseError(msg)

    # Support the original typo key for now.
    root = data.get("workflow") or data.get("worklfow")
    if not isinstance(root, dict):
        msg = "The 'workflow' section must be a mapping"
        raise WorkflowParseError(msg)

    name = str(root.get("name") or workflow_path.stem)
    description = root.get("description")

    parameters_data = root.get("parameters") or []
    steps_data = root.get("steps") or []

    parameters = _parse_parameters(parameters_data)
    steps = _parse_steps_list(steps_data)

    return Workflow(
        name=name,
        description=description,
        parameters=parameters,
        steps=steps,
        source_path=workflow_path,
    )


def _parse_parameters(raw: Any) -> List[Parameter]:
    if not raw:
        return []
    if not isinstance(raw, list):
        msg = "workflow.parameters must be a list"
        raise WorkflowParseError(msg)

    params: List[Parameter] = []
    for item in raw:
        if not isinstance(item, dict) or len(item) != 1:
            msg = f"Invalid parameter entry: {item!r}"
            raise WorkflowParseError(msg)
        (name, spec), = item.items()
        description = None
        required = False
        default = None

        if isinstance(spec, str):
            description = spec
        elif isinstance(spec, dict):
            description = spec.get("description")
            required = bool(spec.get("required", False))
            default = spec.get("default")
        else:
            msg = f"Unsupported parameter specification for '{name}': {spec!r}"
            raise WorkflowParseError(msg)

        params.append(
            Parameter(
                name=str(name),
                description=description,
                required=required,
                default=default,
            )
        )

    return params


def _parse_steps_list(raw: Any) -> List[Step]:
    if not raw:
        return []
    if not isinstance(raw, list):
        msg = "workflow.steps must be a list"
        raise WorkflowParseError(msg)

    return [_parse_step(item) for item in raw]


def _parse_step(raw: Any) -> Step:
    if not isinstance(raw, dict):
        msg = f"Each step must be a mapping, got: {raw!r}"
        raise WorkflowParseError(msg)

    command_name = _detect_command_name(raw)
    if not command_name:
        msg = f"Could not determine command name for step: {raw!r}"
        raise WorkflowParseError(msg)

    args: Dict[str, Any] = {}
    primary_value = raw.get(command_name)

    # Inline value or nested mapping.
    if isinstance(primary_value, dict):
        for key, value in primary_value.items():
            if key in {"then", "else", "do"} and isinstance(value, list):
                args[key] = _parse_steps_list(value)
            else:
                args[key] = value
    elif primary_value is not None:
        # Store scalar values under the generic 'value' key.
        args["value"] = primary_value

    # Merge modifier keys that are siblings of the command name.
    for key, value in raw.items():
        if key == command_name:
            continue
        if key in {"then", "else", "do"} and isinstance(value, list):
            args[key] = _parse_steps_list(value)
        else:
            args[key] = value

    return Step(command=command_name, args=args)


def _detect_command_name(step_mapping: Dict[str, Any]) -> str | None:
    for key in step_mapping.keys():
        if key not in _MODIFIER_KEYS:
            return str(key)
    return None

