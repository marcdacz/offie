## Contributing: adding new commands to Offie

This guide outlines the steps to add a new Offie command, including code, tests, and documentation.

---

## Overview

When you add a command, you should:

1. Design the command's purpose and arguments.
2. Implement the command and wire it into the executor/validator.
3. Add tests that cover both happy and error paths.
4. Document the command in the appropriate docs files.

---

## 1. Design the command

Before writing code, decide:

- **Name**: short, descriptive command name (for example, `http_request`, `run_shell`).
- **Purpose**: one concise sentence describing what it does.
- **Arguments**: required and optional fields, including their types and defaults.
- **Side effects**: what it reads or writes (variables, external systems, output).

Capture this as a short comment or design note near the implementation.

---

## 2. Implement the command

Implementation details will vary by project structure, but in general:

- Add the command implementation alongside existing commands.
- Ensure it:
  - Accepts arguments via the common `Step` / context model.
  - Uses the shared context for reading and writing variables.
  - Reports errors clearly when required arguments are missing or invalid.

Follow existing commands (such as `print`, `set_variable`, or control-flow commands) as patterns for style and behavior.

---

## 3. Add tests

Add or extend tests to cover:

- **Validation**:
  - Missing required arguments.
  - Invalid argument combinations.
  - Unknown command handling if relevant.
- **Execution**:
  - Happy-path behavior.
  - Edge cases and error conditions that should raise.

Use the existing test modules (for example, `tests/test_control_flow.py`, `tests/test_validator.py`, `tests/test_executor.py`) as references for structure and naming.

Run the full test suite:

```bash
pytest
```

---

## 4. Document the command

Update documentation in these places:

- **Command docs** under [`docs/commands/`](commands/):
  - Add the command to the appropriate group page (for example, control flow, variables, output) with:
    - 1–2 line summary.
    - Syntax snippet.
    - Argument descriptions.
    - Small example.
  - If it defines a new group, create a new file (for example, `docs/commands/http.md`) and link it from `docs/commands/README.md`.

Keep examples short and copy-pasteable.

---

## 5. Final checks

Before opening a pull request:

- Ensure all tests pass (`pytest`).
- Confirm documentation builds or renders correctly (if applicable).
- Check that your new command is linked from the relevant `docs/commands/` page(s).

Keeping code, tests, and docs in sync makes it easier for others to discover and use new commands.

***
