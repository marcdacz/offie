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

## Pre-commit hooks

This repo uses [`pre-commit`](https://pre-commit.com/) to keep the codebase tidy and consistent. It uses a modern, minimal setup based on Ruff for both formatting and linting, plus a few lightweight sanity checks (YAML/TOML validation, trailing whitespace, etc.). Tests run as a pre-push hook so regular commits stay fast.

### Installing pre-commit

First, install `pre-commit` in your environment:

```bash
pip install pre-commit
```

Then install the hooks defined in `.pre-commit-config.yaml`:

```bash
pre-commit install
pre-commit install --hook-type pre-push
```

- **`pre-commit install`**: runs the configured checks on every commit.
- **`pre-commit install --hook-type pre-push`**: additionally runs the pre-push hooks (for example, `pytest`) whenever you push.

### Running hooks manually

You can also trigger the hooks manually, without committing:

- **Run all hooks on all files** (useful right after cloning or updating the config):

```bash
pre-commit run --all-files
```

- **Run all hooks on staged files** (same as what happens on commit):

```bash
pre-commit run
```

- **Run a single hook by name** (for example, Ruff):

```bash
pre-commit run ruff --all-files
# or only on staged files:
pre-commit run ruff
```

- **Run pre-push hooks (for example, tests) without pushing:**

```bash
pre-commit run --hook-stage push --all-files
# or, on staged/changed files only:
pre-commit run --hook-stage push
```

If any hook fails, fix the reported issues and re-run the command (or your commit/push) until everything passes.

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
