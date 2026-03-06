## Control flow commands

Control flow commands let a workflow branch and loop over data.

Commands covered here:

- `if`
- `while`
- `for_each`
- `for`

---

## `if`

**Purpose**: Conditionally execute one of two blocks of steps.

**Syntax (YAML)**:

```yaml
- if: "{{name}} == 'Marc'"
  then:
    - print: "Inside an if statement: Hello, Marc!"
  else:
    - print: "Inside an else statement: Hello, {{name}}!"
```

**Arguments**:

- **Inline value / `value`** (required): condition expression.
- **`then`** (required): list of steps to run when the condition is true.
- **`else`** (optional): list of steps to run when the condition is false.

---

## `while`

**Purpose**: Repeat a block of steps while a condition is true.

**Syntax (YAML)**:

```yaml
- set_variable: 1
  as: counter
- while: "{{counter}} <= 5"
  do:
    - print: "Running a while loop: Hello, {{name}} counter is {{counter}}!"
    - set_variable: "{{counter}} + 1"
      as: counter
```

**Arguments**:

- **Inline value / `value`** (required): loop condition expression.
- **`do`** (required): list of steps to execute on each iteration.
- **`max_iterations`** (optional): maximum number of iterations before the loop fails.  
  Defaults to `1000` to protect against infinite loops; increase cautiously if you expect a long‑running loop.

---

## `for_each`

**Purpose**: Iterate over each element in a list.

**Syntax (YAML)**:

```yaml
- set_variable: ["alpha", "beta", "gamma"]
  as: items
- for_each: "{{items}}"
  as: item
  do:
    - print: "Item: {{item}}"
```

**Arguments**:

- **Inline value / `value`** (required): expression that evaluates to an iterable.
- **`as`** (required): variable name for the current item.
- **`do`** (required): list of steps to run for each item.

---

## `for`

**Purpose**: Iterate over a numeric range.

**Syntax (YAML)**:

```yaml
- for:
    start: 0
    end: 3
    as: index
    do:
      - print: "Index is {{index}}"
```

**Arguments**:

- **`start`** (required): starting integer (inclusive).
- **`end`** (required): ending integer (exclusive).
- **`as`** (required): variable name for the current index.
- **`do`** (required): list of steps to run for each index.

