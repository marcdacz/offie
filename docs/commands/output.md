## Output commands

Output commands print information from your workflow.

Commands covered here:

- `print`
- `log`

---

## `print`

**Purpose**: Print a message to standard output with optional variable interpolation.

**Syntax (inline)**:

```yaml
- print: "Hello, {{name}}!"
```

**Syntax (expanded)**:

```yaml
- print:
    message: "Hello, {{name}}!"
```

**Arguments**:

- **Inline value**: treated as `message`.
- **`message`** (expanded form): string to print.

**Example**:

```yaml
steps:
  - set_variable:
      value: "World"
    as: name
  - print: "Hello, {{name}}!"
```

---

## `log`

**Purpose**: Emit a log message at a given level. Messages only appear when the CLI `--loglevel` is at or above the message level (e.g. with `--loglevel=debug`, debug messages show; with default `info`, they do not). Useful for debugging and progress in workflows.

**Log line format**: Each line includes an ISO 8601 timestamp, uppercase level (DEBUG, INFO, WARNING, ERROR), then the message. Example: `2025-03-08T14:30:00.123456 INFO Log message here.`

**Syntax (expanded)**:

```yaml
- log:
    level: debug
    message: Log message here.
```

**Arguments**:

- **`message`** (required): string to log. Supports `{{variable}}` interpolation.
- **`level`** (optional): one of `debug`, `info`, `warning`, `error`. Default: `info`.

**Example**:

```yaml
steps:
  - log:
      message: "Starting phase 1"
      level: info
  - log:
      level: debug
      message: "Debug detail: {{some_var}}"
```

With `--loglevel=info`, only the first message is shown. With `--loglevel=debug`, both are shown.
