from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Mapping, Optional, Type

from offie.core.models import Step


class BaseCommand(ABC):
    """
    Base class for all commands.
    """

    #: Command name as it appears in the YAML DSL.
    name: str
    #: Names of required arguments in Step.args.
    required_args: List[str] = []
    #: Names of optional arguments in Step.args.
    optional_args: List[str] = []

    def validate(self, step: Step) -> List[str]:
        """
        Validate arguments for this command.

        Concrete commands can override to add more specific checks.
        """

        errors: List[str] = []
        for arg in self.required_args:
            if arg not in step.args:
                errors.append(f"Missing required argument '{arg}' for command '{self.name}'")
        return errors

    @abstractmethod
    def execute(self, step: Step, context: Any, executor: Any) -> None:  # pragma: no cover - interface only
        """
        Execute this command.
        """


class CommandRegistry:
    """
    Registry mapping command names to their implementing classes.
    """

    def __init__(self) -> None:
        self._commands: Dict[str, Type[BaseCommand]] = {}

    def register(self, command_cls: Type[BaseCommand]) -> Type[BaseCommand]:
        name = getattr(command_cls, "name", None)
        if not name:
            msg = "Command classes must define a non-empty 'name' attribute"
            raise ValueError(msg)
        self._commands[name] = command_cls
        return command_cls

    def get(self, name: str) -> Optional[Type[BaseCommand]]:
        return self._commands.get(name)

    def all(self) -> Mapping[str, Type[BaseCommand]]:
        return dict(self._commands)


registry = CommandRegistry()


def command(cls: Type[BaseCommand]) -> Type[BaseCommand]:
    """
    Decorator to register a command class in the global registry.
    """

    return registry.register(cls)

