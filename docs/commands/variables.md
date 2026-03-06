## Variable commands

Variable commands let you create and update workflow variables.

Commands covered here:

- `set_variable`

---

## `set_variable`

**Purpose**: Compute a value and store it in a variable.

**Syntax (YAML)**:

```yaml
- set_variable:
    value: "{{counter}} + 1"
  as: counter
```

**Arguments**:

- **`value`** (required): expression or literal to assign.
- **`as`** (required): variable name to store the result in.

**Example**:

```yaml
steps:
  - set_variable:
      value: 1
    as: counter
  - set_variable:
      value: "{{counter}} + 1"
    as: counter
  - print: "Counter is now {{counter}}"
```

