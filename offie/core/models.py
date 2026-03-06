from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Parameter:
    """
    Represents a top-level workflow parameter.
    """

    name: str
    description: str | None = None
    required: bool = False
    default: Any = None


@dataclass
class Step:
    """
    Represents a single workflow step.
    """

    command: str
    args: dict[str, Any] = field(default_factory=dict)


@dataclass
class Workflow:
    """
    In-memory representation of a workflow definition.
    """

    name: str
    description: str | None
    parameters: list[Parameter] = field(default_factory=list)
    steps: list[Step] = field(default_factory=list)
    source_path: Path | None = None
