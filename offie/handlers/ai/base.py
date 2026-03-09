from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any


class BaseAIHandler(ABC):
    """
    Base class for AI providers (Ollama, OpenAI, etc.).
    """

    #: Handler name as used in workflow YAML (e.g. "ollama").
    name: str
    #: Default model when not specified in the step.
    default_model: str | None = None

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        options: dict[str, Any] | None = None,
        log_level: str = "info",
    ) -> str:
        """
        Send the prompt to the AI and return the raw text response.

        options: handler-specific input from the workflow (e.g. model, source_repository).
        Handlers read options.get("model") and use default_model if absent.
        log_level: minimum log level for any progress/debug logs the handler may emit.
        """


class AIHandlerRegistry:
    """
    Registry mapping handler names to their implementing classes.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, type[BaseAIHandler]] = {}

    def register(self, handler_cls: type[BaseAIHandler]) -> type[BaseAIHandler]:
        name = getattr(handler_cls, "name", None)
        if not name:
            msg = "Handler classes must define a non-empty 'name' attribute"
            raise ValueError(msg)
        self._handlers[name] = handler_cls
        return handler_cls

    def get(self, name: str) -> type[BaseAIHandler] | None:
        return self._handlers.get(name)

    def all(self) -> Mapping[str, type[BaseAIHandler]]:
        return dict(self._handlers)


registry = AIHandlerRegistry()


def ai_handler(cls: type[BaseAIHandler]) -> type[BaseAIHandler]:
    """
    Decorator to register an AI handler class in the global registry.
    """
    return registry.register(cls)
