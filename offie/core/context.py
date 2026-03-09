from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

_TEMPLATE_START = "{{"
_TEMPLATE_END = "}}"


@dataclass
class Context:
    """
    Holds workflow and system variables.
    """

    workflow_name: str
    workflow_file: Path
    log_level: str = "info"
    _system: dict[str, Any] = field(default_factory=dict, init=False, repr=False)
    _workflow: dict[str, Any] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        now = datetime.now()
        self._system.update(
            {
                "date": now.date().isoformat(),
                "time": now.time().isoformat(timespec="seconds"),
                "timestamp": now.isoformat(),
                "os": os.name,
                "platform": os.sys.platform,
                "cwd": os.getcwd(),
                "workflow_name": self.workflow_name,
                "workflow_file": str(self.workflow_file),
            }
        )

    # ------------------------------------------------------------------
    # Variable access
    # ------------------------------------------------------------------
    @property
    def system(self) -> Mapping[str, Any]:
        return dict(self._system)

    @property
    def workflow(self) -> Mapping[str, Any]:
        return dict(self._workflow)

    def get(self, name: str) -> Any:
        if name.startswith("sys."):
            key = name.split(".", 1)[1]
            if key in self._system:
                return self._system[key]
            msg = f"Unknown system variable '{name}'"
            raise KeyError(msg)

        if name in self._workflow:
            return self._workflow[name]

        msg = f"Unknown workflow variable '{name}'"
        raise KeyError(msg)

    def set(self, name: str, value: Any) -> None:
        if name.startswith("sys."):
            msg = f"Cannot overwrite read-only system variable '{name}'"
            raise ValueError(msg)
        self._workflow[name] = value

    # ------------------------------------------------------------------
    # Template / expression support
    # ------------------------------------------------------------------
    def as_expression_names(self) -> dict[str, Any]:
        """
        Return the mapping used for expression evaluation.

        System variables are exposed under the `sys` namespace, while
        workflow variables are exposed at the top level.
        """

        names: dict[str, Any] = {"sys": dict(self._system)}
        names.update(self._workflow)
        return names

    def render_template(self, value: Any) -> Any:
        """
        Render `{{var}}` placeholders in a string using current variables.
        Non-string values are returned unchanged.
        """

        if not isinstance(value, str):
            return value

        result = ""
        i = 0
        text = value
        while i < len(text):
            start = text.find(_TEMPLATE_START, i)
            if start == -1:
                result += text[i:]
                break

            result += text[i:start]
            end = text.find(_TEMPLATE_END, start + len(_TEMPLATE_START))
            if end == -1:
                # No closing tag; treat the rest as literal.
                result += text[start:]
                break

            expr = text[start + len(_TEMPLATE_START) : end].strip()
            result += str(self._resolve_variable(expr))
            i = end + len(_TEMPLATE_END)

        return result

    def _resolve_variable(self, name: str) -> Any:
        """
        Resolve a dotted variable name like `sys.workflow_name`.
        """

        parts = name.split(".")
        if not parts:
            msg = "Empty variable name in template"
            raise ValueError(msg)

        # `sys.*` variables are always taken from the system mapping.
        if parts[0] == "sys":
            current: Any = dict(self._system)
        else:
            current = dict(self._workflow)

        for i, part in enumerate(parts):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                # Fall back to top-level workflow variables only for the first part.
                if parts[0] != "sys" and i == 0 and part in self._workflow:
                    current = self._workflow[part]
                    continue
                # Missing nested key: return "".
                if i > 0 and isinstance(current, dict):
                    return ""
                msg = f"Unknown variable '{name}' in template"
                raise KeyError(msg)

        return current
