"""Built-in and custom command implementations for Offie."""

# Import built-in commands so they register themselves with the global registry.
from . import control_flow  # noqa: F401
from . import output  # noqa: F401
from . import variables  # noqa: F401
