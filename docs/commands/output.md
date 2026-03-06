## Output commands

Output commands print information from your workflow.

Commands covered here:

- `print`

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

