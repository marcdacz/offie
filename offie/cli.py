from __future__ import annotations

import argparse
import sys
from typing import Any

from offie.core.executor import Executor
from offie.core.parser import load_workflow
from offie.core.validator import ValidationError, validate_workflow


def _parse_parameter_overrides(values: list[str]) -> dict[str, Any]:
    overrides: dict[str, Any] = {}
    for raw in values:
        if "=" not in raw:
            msg = f"Invalid parameter override '{raw}', expected key=value"
            raise ValueError(msg)
        key, value = raw.split("=", 1)
        key = key.strip()
        if not key:
            msg = f"Invalid parameter name in override '{raw}'"
            raise ValueError(msg)
        overrides[key] = value
    return overrides


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Offie workflow runner")
    parser.add_argument("workflow_file", help="Path to the workflow YAML file")
    parser.add_argument(
        "-p",
        "--parameter",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Override a top-level workflow parameter (can be used multiple times)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        parameter_overrides = _parse_parameter_overrides(args.parameter)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    workflow = load_workflow(args.workflow_file)

    errors: list[ValidationError] = validate_workflow(workflow)
    if errors:
        print("Workflow validation failed:", file=sys.stderr)
        for err in errors:
            print(f" - [{err.location}] {err.message}", file=sys.stderr)
        return 1

    executor = Executor()
    try:
        executor.execute(workflow, cli_parameters=parameter_overrides)
    except Exception as exc:
        print(f"Workflow execution failed: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
