## Offie

Offie is a small Python tool that executes workflows defined in a simple YAML-based DSL so you can describe and run automation as readable YAML files.

---

## Quickstart

1. **Ensure you have Python 3.10+ and `pip` installed**

You can check your Python version with:

```bash
python --version
```

2. **Clone the repo**

```bash
git clone <your-fork-or-repo-url>
cd offie
```

3. **Install Offie in editable mode**

```bash
pip install -e .
```

4. **Run the basic workflow**

```bash
offie workflows/basic_workflow.yml -p team_name="Platform" --parameter greeting="Good morning"
```

This parses the workflow, validates it, and executes each step while printing output to your terminal.

---

## What next

- **Getting started tutorial**: [`docs/getting-started.md`](docs/getting-started.md) – install Offie, learn the CLI, and run the example workflow.
- **Command reference**: explore available commands under [`docs/commands/`](docs/commands/).

---

## Tests

Run the test suite with:

```bash
pytest
```

---

## YAML DSL Overview

Workflows are defined under a top-level `workflow` key:

```yaml
workflow:
  name: Basic Team Check-in
  description: >
    Example workflow that demonstrates parameters, workflow variables,
    system variables, and nested control flow.

  parameters:
    - team_name:
        description: Name of the team running the check-in.
        default: "Platform"
    - greeting:
        description: Greeting prefix used in messages.
        default: "Hello"

  steps:
    - set_variable: "{{sys.workflow_name}}"
      as: workflow_name
    - set_variable: "{{sys.workflow_file}}"
      as: workflow_file
    - set_variable: "{{sys.date}}"
      as: run_date
    - set_variable: "{{sys.time}}"
      as: run_time
    - print: "=== Running '{{workflow_name}}' from {{workflow_file}} ==="
    - print: "Date: {{run_date}} Time: {{run_time}}"
    - set_variable:
        value: '{{greeting}} + " " + {{team_name}} + " team!"'
      as: welcome_message
    - print: "{{welcome_message}}"
```

- **Parameters** define top-level inputs that can be overridden via `-p/--parameter` on the CLI.
- **Steps** are a list of commands; each command can have inline values and/or additional keys such as `as`, `then`, `else`, `do`, `start`, `end`.

Control-flow commands:

- `print` – print a message (inline or via `message:`) with `{{var}}` interpolation
- `set_variable` – compute a `value` and store it under `as`
- `if` – conditional execution with `condition`, `then`, `else`
- `while` – loop with `condition` and `do` steps
- `for_each` – iterate over a list with `value`, `as`, `do`
- `for` – numeric loop with `start`, `end`, `as`, `do`

System variables (read-only) are exposed under the `sys.` namespace (e.g. `sys.workflow_name`, `sys.date`), while workflow variables are global and mutable.
