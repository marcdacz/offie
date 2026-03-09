## AI agent commands

AI agent commands call external language models and store structured results in workflow variables for use in later steps.

Commands covered here:

- `call_ai_agent`

---

## `call_ai_agent`

**Purpose**: Send a prompt to an AI provider (e.g. Ollama), receive a JSON response, and store the parsed result plus system metadata in a variable. The response is kept in memory only; later steps can access it via `{{variable.key}}` and `{{variable.__metadata.*}}`.

**Syntax (YAML)**:

```yaml
- call_ai_agent:
    handler: ollama
    model: qwen3:4b   # optional
    prompt: |
      Return a JSON object with keys: summary, confidence, suggestions.
      Topic: {{topic}}
  as: analysis
```

**Arguments**:

- **`handler`** (required): Name of the AI provider to use (e.g. `ollama`). Must be registered in the AI handler registry.
- **`prompt`** (required): The user prompt. Supports `{{variable}}` interpolation; the command resolves placeholders before sending the prompt to the AI.
- **`as`** (required): Variable name to store the result in. The value is a dict: the AI's JSON plus a system-generated `__metadata` block.
- **`model`** (optional): Model to use for this step. If omitted, the handler's default model is used. You can also set `options.model`; the top-level `model` overrides `options.model` when both are present.
- **`options`** (optional): Handler-specific key-value input. String values support `{{variable}}` interpolation. Each handler documents its own options (e.g. `source_repository` for Cursor). The handler also receives `model` here when you set it at the top level or under `options`.

**Environment and .env**

Offie loads a `.env` file from the current working directory at startup. You can put API keys there (e.g. `CURSOR_API_KEY=key_...`) so handlers that need them work without exporting variables in the shell. Keep `.env` out of version control; use a `.env.example` with placeholder keys and no real secrets.

**Output structure**

The value stored in `as` is always a dict with at least:

- **User-facing keys**: Whatever the AI returns as top-level JSON (e.g. `summary`, `confidence`, `suggestions`).
- **`__metadata`** (always present): System-generated metadata:
  - `handler`: Provider name (e.g. `ollama`).
  - `model`: Model used (from the step or the handler default).
  - `execution_duration`: Time taken for the call (e.g. `"2.34s"`).
  - `output_files`: Reserved for future use; currently an empty list.
  - `parse_error`: Present only when no valid JSON could be extracted from the response. In that case the raw response is stored under the `response` key.

The AI is instructed to respond with **JSON only** (no markdown or extra text) so that parsing is reliable. If the raw response is not directly parseable as JSON (e.g. markdown fences, surrounding prose), the command automatically tries to extract a JSON object from the text before falling back to the raw response.

**Example**

```yaml
workflow:
  name: AI Demo
  parameters:
    - topic:
        default: "benefits of automated testing"
  steps:
    - call_ai_agent:
        handler: ollama
        prompt: |
          Return a JSON object with keys: summary (one sentence), confidence (0-100), suggestions (array of 2 strings).
          Topic: {{topic}}
      as: analysis

    - print: "Summary: {{analysis.summary}}"
    - print: "Confidence: {{analysis.confidence}}"
    - print: "Duration: {{analysis.__metadata.execution_duration}}"
```

**Errors**

- **Unknown handler**: If `handler` is not registered, the command raises a runtime error listing available handlers.
- **Connection failure** (e.g. Ollama not running): The handler may raise a `RuntimeError` with a message indicating the service is unreachable.
- **Invalid JSON**: The command does not fail; it stores the raw response under `response` and records the error in `__metadata.parse_error`.

**Built-in handlers**

- **`ollama`**: Local models via [Ollama](https://ollama.com). Default model: `qwen3:4b`. Requires Ollama running (e.g. `ollama serve`) and a pulled model. No extra options required.
  Runtime logging behavior:
  - With `--loglevel info`, streamed assistant output is shown in real time as inline text (not one timestamped log line per token), including thinking text when the model provides it.
  - With `--loglevel debug`, you also see handler lifecycle logs (request setup and call details).
  - Empty/whitespace-only stream chunks are ignored to keep terminal output readable.

- **`cursor`**: [Cursor Cloud Agents API](https://cursor.com/docs/cloud-agent/api/overview). Requires `CURSOR_API_KEY` in the environment (or in `.env`). Options:
  - **`source_repository`** (required): GitHub repository URL (e.g. `https://github.com/your-org/your-repo`).
  - **`ref`** (optional): Branch, tag, or commit (e.g. `main`).
  - **`model`** (optional): Model ID or `"default"`; see Cursor docs for available models.
  The handler launches a cloud agent, polls until it finishes, and uses the **last assistant message** from the conversation as the response (result body is dynamic). JSON is automatically extracted from the message even if it is wrapped in markdown fences or surrounded by prose.
  Runtime logging behavior:
  - With `--loglevel info` (default), assistant messages are streamed to the terminal as they are received.
  - With `--loglevel debug`, you also see handler lifecycle logs (request setup, polling, etc.).
  - With `--loglevel warning` or higher, streamed assistant messages are not printed (the handler still returns the last message for the workflow).

Example with Cursor:

```yaml
- call_ai_agent:
    handler: cursor
    prompt: "Return JSON with key summary about this repo."
    options:
      source_repository: "https://github.com/your-org/your-repo"
      ref: main
  as: result
```

Additional providers can be added by implementing the AI handler interface and registering with the `@ai_handler` decorator; see the codebase under `offie/handlers/ai/`.
