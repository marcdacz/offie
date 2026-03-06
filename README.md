## Offie

Offie is a small Python tool that executes workflows defined in a simple YAML-based DSL.  

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

4. **Run the example workflow**

```bash
offie workflows/example.yml -p parameter_name_1=hello --parameter parameter_name_2=world
```

This will parse the workflow, validate it, and execute the steps while printing output to your terminal.

---

## YAML DSL Overview

Workflows are defined under a top-level `workflow` key:

```yaml
workflow:
  name: Example Base Workflow
  description: Demo of control flow commands.

  parameters:
    - parameter_name_1: parameter_description_1
    - parameter_name_2: parameter_description_2

  steps:
    - set_variable:
        value: Marc
      as: name
    - print: "Hello, {{name}}!"
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
