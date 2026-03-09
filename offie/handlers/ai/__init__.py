"""AI handler registry and base for call_ai_agent command."""

# Import built-in handlers so they register when this package is loaded.
from offie.handlers.ai import (
    cursor,  # noqa: F401 - registers CursorHandler
    ollama,  # noqa: F401 - registers OllamaHandler
)
from offie.handlers.ai.base import (
    AIHandlerRegistry,
    BaseAIHandler,
    ai_handler,
    registry,
)

__all__ = [
    "AIHandlerRegistry",
    "BaseAIHandler",
    "ai_handler",
    "registry",
]
