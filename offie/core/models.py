from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Parameter:
    """
    Represents a top-level workflow parameter.
    """

    name: str
    description: Optional[str] = None
    required: bool = False
    default: Any = None


@dataclass
class Step:
    """
    Represents a single workflow step.
    """

    command: str
    args: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Workflow:
    """
    In-memory representation of a workflow definition.
    """

    name: str
    description: Optional[str]
    parameters: List[Parameter] = field(default_factory=list)
    steps: List[Step] = field(default_factory=list)
    source_path: Optional[Path] = None

