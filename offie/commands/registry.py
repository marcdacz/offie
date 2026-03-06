from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from offie.core.models import Step


class BaseCommand(ABC):
    """
    Base class for all commands.
    """

    #: Command name as it appears in the YAML DSL.
    name: str
    #: Names of required arguments in Step.args.
    required_args: list[str] = []
    #: Names of optional arguments in Step.args.
    optional_args: list[str] = []

    def validate(self, step: Step) -> list[str]:
        """
        Validate arguments for this command.

        Concrete commands can override to add more specific checks.
        """

        errors: list[str] = []
        for arg in self.required_args:
            if arg not in step.args:
                errors.append(f"Missing required argument '{arg}' for command '{self.name}'")
        return errors

    @abstractmethod
    def execute(
        self, step: Step, context: Any, executor: Any
    ) -> None:  # pragma: no cover - interface only
        """
        Execute this command.
        """


class CommandRegistry:
    """
    Registry mapping command names to their implementing classes.
    """

    def __init__(self) -> None:
        self._commands: dict[str, type[BaseCommand]] = {}

    def register(self, command_cls: type[BaseCommand]) -> type[BaseCommand]:
        name = getattr(command_cls, "name", None)
        if not name:
            msg = "Command classes must define a non-empty 'name' attribute"
            raise ValueError(msg)
        self._commands[name] = command_cls
        return command_cls

    def get(self, name: str) -> type[BaseCommand] | None:
        return self._commands.get(name)

    def all(self) -> Mapping[str, type[BaseCommand]]:
        return dict(self._commands)


registry = CommandRegistry()


def command(cls: type[BaseCommand]) -> type[BaseCommand]:
    """
    Decorator to register a command class in the global registry.
    """

    return registry.register(cls)
