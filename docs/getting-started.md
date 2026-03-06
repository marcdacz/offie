## Getting started with Offie

Offie executes workflows written in a simple YAML-based DSL. This guide shows how to install Offie, understand the CLI, and run the bundled example workflow.

---

## 1. Install Offie

**Requirements**

- Python 3.10+
- `pip`

Install from a clone:

```bash
git clone <your-fork-or-repo-url>
cd offie
pip install -e .
```

This installs the `offie` CLI in your environment.

---

## 2. CLI basics

General form:

```bash
offie WORKFLOW_FILE [OPTIONS]
```

- **`WORKFLOW_FILE`**: path to a YAML file with a top-level `workflow` key.
- **Parameters**:
  - `-p NAME=VALUE` or `--parameter NAME=VALUE`
  - May be passed multiple times to override workflow parameters.

Example:

```bash
offie workflows/basic_workflow.yml \
  -p team_name="Platform" \
  --parameter greeting="Good morning"
```

Exit codes:

- `0` – workflow executed successfully.
- non-zero – parse, validation, or runtime error.

---

## 3. Run the basic workflow

The repo ships with `workflows/basic_workflow.yml`, which demonstrates:

- Workflow parameters and interpolation (`team_name`, `greeting`, `attendees`).
- System variables such as `{{sys.date}}`, `{{sys.time}}`, and `{{sys.workflow_name}}`.
- Control flow commands: conditionals (`if` with `then` / `else`) and loops (`while`, `for_each`, `for`), including nested loops and nested `if` blocks.

Run it:

```bash
offie workflows/basic_workflow.yml \
  -p team_name="Platform" \
  --parameter greeting="Good morning"
```

You should see:

- A header showing the workflow name, file path, current date, and time.
- A personalised greeting for the team.
- Per-attendee check-ins, including a special message for one attendee.
- Multiple stand-up rounds with nested loops over status values and `if` branches for blocked items.
- A short numeric summary section that prints several summary lines.

---

## 4. Next steps

- Open `workflows/basic_workflow.yml` and tweak values (parameters, conditions, loops) to see how behavior changes.
- Explore command docs under [`docs/commands/`](commands/) for details on available commands.

