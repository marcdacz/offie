from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from offie.commands.ai import CallAIAgentCommand
from offie.core.context import Context
from offie.core.models import Step, Workflow
from offie.core.validator import validate_workflow
from offie.handlers.ai.base import BaseAIHandler
from offie.handlers.ai.base import registry as ai_registry
from offie.handlers.ai.cursor import CursorHandler
from offie.handlers.ai.ollama import OllamaHandler

# ---------------------------------------------------------------------------
# AI handler registry
# ---------------------------------------------------------------------------


def registry__should_return_handler_class__when_name_was_registered() -> None:
    class FakeHandler(BaseAIHandler):
        name = "fake"
        default_model = "fake-model"

        def generate(
            self,
            prompt: str,
            system_prompt: str | None = None,
            options: dict | None = None,
            log_level: str = "info",
        ) -> str:
            return "{}"

    ai_registry.register(FakeHandler)
    try:
        cls = ai_registry.get("fake")
        assert cls is FakeHandler
        assert ai_registry.all().get("fake") is FakeHandler
    finally:
        ai_registry._handlers.pop("fake", None)


def registry__should_return_none__when_name_is_unknown() -> None:
    assert ai_registry.get("nonexistent_handler_xyz") is None


# ---------------------------------------------------------------------------
# CallAIAgentCommand validation
# ---------------------------------------------------------------------------


def validate_workflow__should_accept_workflow__when_call_ai_agent_has_required_args() -> None:
    workflow = Workflow(
        name="ai-workflow",
        description=None,
        parameters=[],
        steps=[
            Step(
                command="call_ai_agent",
                args={"handler": "ollama", "prompt": "Say hello", "as": "result"},
            ),
        ],
        source_path=None,
    )

    errors = validate_workflow(workflow)

    assert errors == []


def validate_workflow__should_reject_workflow__when_call_ai_agent_missing_required_args() -> None:
    workflow = Workflow(
        name="ai-workflow",
        description=None,
        parameters=[],
        steps=[
            Step(
                command="call_ai_agent",
                args={"handler": "ollama"},
            ),
        ],
        source_path=None,
    )

    errors = validate_workflow(workflow)

    messages = [e.message for e in errors]
    assert any("call_ai_agent requires 'prompt'" in m for m in messages)
    assert any("call_ai_agent requires 'as'" in m for m in messages)


# ---------------------------------------------------------------------------
# CallAIAgentCommand execution (mocked handler)
# ---------------------------------------------------------------------------


def _make_fake_handler(
    response: str,
    record_options: list | None = None,
) -> type[BaseAIHandler]:
    class FakeHandler(BaseAIHandler):
        name = "fake"
        default_model = "fake-model"

        def generate(
            self,
            prompt: str,
            system_prompt: str | None = None,
            options: dict | None = None,
            log_level: str = "info",
        ) -> str:
            if record_options is not None:
                record_options.append(options)
            return response

    return FakeHandler


def call_ai_agent__should_store_parsed_json_with_metadata__when_handler_returns_valid_json() -> (
    None
):
    workflow_file = Path("/tmp/workflow.yml")
    context = Context(workflow_name="test", workflow_file=workflow_file)
    context.set("input_var", "hello")

    step = Step(
        command="call_ai_agent",
        args={
            "handler": "ollama",
            "prompt": "Return JSON with key x equal to {{input_var}}",
            "as": "out",
        },
    )

    fake_response = '{"x": "hello", "score": 42}'

    with patch("offie.commands.ai.ai_registry.get", return_value=_make_fake_handler(fake_response)):
        command = CallAIAgentCommand()
        command.execute(step, context, None)

    result = context.get("out")
    assert result["x"] == "hello"
    assert result["score"] == 42
    assert "__metadata" in result
    meta = result["__metadata"]
    assert meta["handler"] == "ollama"
    assert "execution_duration" in meta
    assert meta["output_files"] == []


def call_ai_agent__should_store_raw_response__when_handler_returns_invalid_json() -> None:
    workflow_file = Path("/tmp/workflow.yml")
    context = Context(workflow_name="test", workflow_file=workflow_file)

    step = Step(
        command="call_ai_agent",
        args={"handler": "ollama", "prompt": "Hi", "as": "out"},
    )

    with patch(
        "offie.commands.ai.ai_registry.get",
        return_value=_make_fake_handler("not valid json at all"),
    ):
        command = CallAIAgentCommand()
        command.execute(step, context, None)

    result = context.get("out")
    assert result["response"] == "not valid json at all"
    assert "__metadata" in result
    assert "parse_error" in result["__metadata"]
    assert "No valid JSON" in result["__metadata"]["parse_error"]


def call_ai_agent__should_pass_options_to_handler__when_options_and_model_provided() -> None:
    workflow_file = Path("/tmp/workflow.yml")
    context = Context(workflow_name="test", workflow_file=workflow_file)

    recorded: list = []
    step = Step(
        command="call_ai_agent",
        args={
            "handler": "ollama",
            "prompt": "Hi",
            "as": "out",
            "model": "custom-model",
            "options": {"key": "value", "nested": {"ref": "main"}},
        },
    )

    with patch(
        "offie.commands.ai.ai_registry.get",
        return_value=_make_fake_handler('{"ok": true}', record_options=recorded),
    ):
        command = CallAIAgentCommand()
        command.execute(step, context, None)

    assert len(recorded) == 1
    opts = recorded[0]
    assert opts is not None
    assert opts.get("model") == "custom-model"
    assert opts.get("key") == "value"
    assert opts.get("nested") == {"ref": "main"}


def call_ai_agent__should_raise_runtime_error__when_handler_name_is_unknown() -> None:
    workflow_file = Path("/tmp/workflow.yml")
    context = Context(workflow_name="test", workflow_file=workflow_file)

    step = Step(
        command="call_ai_agent",
        args={"handler": "nonexistent_xyz", "prompt": "Hi", "as": "out"},
    )

    command = CallAIAgentCommand()

    with pytest.raises(RuntimeError) as excinfo:
        command.execute(step, context, None)

    assert "Unknown AI handler 'nonexistent_xyz'" in str(excinfo.value)


# ---------------------------------------------------------------------------
# JSON extraction (used by call_ai_agent when json.loads fails)
# ---------------------------------------------------------------------------


def extract_json__should_return_json__when_wrapped_in_markdown_fence() -> None:
    from offie.commands.ai import _extract_json

    text = 'Here is the result:\n\n```json\n{"summary": "hello", "score": 42}\n```\n\nDone!'
    result = _extract_json(text)
    assert result is not None
    import json

    parsed = json.loads(result)
    assert parsed["summary"] == "hello"
    assert parsed["score"] == 42


def extract_json__should_return_json__when_embedded_in_prose() -> None:
    from offie.commands.ai import _extract_json

    text = (
        'I analyzed the repo. {"summary": "A PDF comparison tool", '
        '"confidence": 85} Hope that helps!'
    )
    result = _extract_json(text)
    assert result is not None
    import json

    parsed = json.loads(result)
    assert parsed["summary"] == "A PDF comparison tool"


def extract_json__should_prefer_last_fenced_block__when_multiple_present() -> None:
    from offie.commands.ai import _extract_json

    text = (
        '```json\n{"draft": true}\n```\nActually here is the final:\n'
        '```json\n{"summary": "final"}\n```'
    )
    result = _extract_json(text)
    assert result is not None
    import json

    parsed = json.loads(result)
    assert parsed["summary"] == "final"


def extract_json__should_return_none__when_no_json_present() -> None:
    from offie.commands.ai import _extract_json

    assert _extract_json("no json here at all") is None


def call_ai_agent__should_extract_json_from_fenced_response__when_direct_parse_fails() -> None:
    workflow_file = Path("/tmp/workflow.yml")
    context = Context(workflow_name="test", workflow_file=workflow_file)

    step = Step(
        command="call_ai_agent",
        args={"handler": "ollama", "prompt": "Hi", "as": "out"},
    )

    fenced = 'Here is the result:\n\n```json\n{"summary": "hello", "score": 42}\n```\n'
    with patch(
        "offie.commands.ai.ai_registry.get",
        return_value=_make_fake_handler(fenced),
    ):
        command = CallAIAgentCommand()
        command.execute(step, context, None)

    result = context.get("out")
    assert result["summary"] == "hello"
    assert result["score"] == 42
    assert "__metadata" in result
    assert "parse_error" not in result["__metadata"]


def call_ai_agent__should_merge_extra_metadata__when_handler_provides_it() -> None:
    workflow_file = Path("/tmp/workflow.yml")
    context = Context(workflow_name="test", workflow_file=workflow_file)

    step = Step(
        command="call_ai_agent",
        args={"handler": "ollama", "prompt": "Hi", "as": "out"},
    )

    class FakeWithExtra(BaseAIHandler):
        name = "fake_extra"
        default_model = "fake-model"

        def __init__(self):
            self.extra_metadata = {"messages": ["msg1", "msg2"]}

        def generate(self, prompt, system_prompt=None, options=None, log_level="info"):
            return '{"ok": true}'

    with patch("offie.commands.ai.ai_registry.get", return_value=FakeWithExtra):
        command = CallAIAgentCommand()
        command.execute(step, context, None)

    result = context.get("out")
    assert result["__metadata"]["messages"] == ["msg1", "msg2"]


# ---------------------------------------------------------------------------
# Ollama handler stream output
# ---------------------------------------------------------------------------


class _FakeOllamaStreamResponse:
    def __init__(self, lines: list[str]) -> None:
        self._lines = lines

    def iter_lines(self):
        return iter(self._lines)


def consume_stream__should_log_info_chunks__when_log_level_is_info() -> None:
    handler = OllamaHandler()
    response = _FakeOllamaStreamResponse(
        [
            '{"response":"Hel"}',
            '{"response":"lo","done":true}',
        ]
    )

    with (
        patch("offie.handlers.ai.ollama.output_log") as output_log_mock,
        patch("builtins.print") as print_mock,
    ):
        result = handler._consume_stream(response, "info")

    assert result == "Hello"
    assert output_log_mock.call_count == 1
    assert output_log_mock.call_args[0][0] == "info"
    assert output_log_mock.call_args[0][1] == "Message 1/1:..."
    printed_parts = [call.args[0] for call in print_mock.call_args_list if call.args]
    assert "[Ollama] " in printed_parts
    assert "Hel" in printed_parts
    assert "lo" in printed_parts


def consume_stream__should_skip_empty_chunks__when_response_or_thinking_is_blank() -> None:
    handler = OllamaHandler()
    response = _FakeOllamaStreamResponse(
        [
            '{"thinking":""}',
            '{"response":"   "}',
            '{"thinking":"Plan step"}',
            '{"response":"ok","done":true}',
        ]
    )

    with patch("offie.handlers.ai.ollama.output_log"), patch("builtins.print") as print_mock:
        result = handler._consume_stream(response, "info")

    assert result == "   ok"
    printed_parts = [call.args[0] for call in print_mock.call_args_list if call.args]
    assert "   " not in printed_parts
    assert "Plan step" in printed_parts
    assert "ok" in printed_parts


def consume_stream__should_include_thinking_in_output_logs__when_thinking_field_present() -> None:
    handler = OllamaHandler()
    response = _FakeOllamaStreamResponse(
        [
            '{"thinking":"Need to inspect files"}',
            '{"response":"Done","done":true}',
        ]
    )

    with patch("offie.handlers.ai.ollama.output_log"), patch("builtins.print") as print_mock:
        handler._consume_stream(response, "info")

    printed_parts = [call.args[0] for call in print_mock.call_args_list if call.args]
    assert "[Ollama] [thinking] " in printed_parts
    assert "Need to inspect files" in printed_parts
    assert "[Ollama] " in printed_parts
    assert "Done" in printed_parts


def consume_stream__should_return_only_response_text__when_thinking_is_present() -> None:
    handler = OllamaHandler()
    response = _FakeOllamaStreamResponse(
        [
            '{"thinking":"step 1"}',
            '{"response":"Hello "}',
            '{"thinking":"step 2"}',
            '{"response":"world","done":true}',
        ]
    )

    with patch("offie.handlers.ai.ollama.output_log"):
        result = handler._consume_stream(response, "info")

    assert result == "Hello world"


# ---------------------------------------------------------------------------
# Cursor handler
# ---------------------------------------------------------------------------


def cursor_handler__should_raise__when_CURSOR_API_KEY_missing() -> None:
    with patch.dict("os.environ", {"CURSOR_API_KEY": ""}, clear=False):
        handler = CursorHandler()
        with pytest.raises(RuntimeError) as excinfo:
            handler.generate(
                prompt="Hi",
                options={"source_repository": "https://github.com/org/repo"},
            )
        assert "CURSOR_API_KEY" in str(excinfo.value)


def cursor_handler__should_raise__when_source_repository_missing() -> None:
    with patch.dict("os.environ", {"CURSOR_API_KEY": "key_test"}):
        handler = CursorHandler()
        with pytest.raises(RuntimeError) as excinfo:
            handler.generate(prompt="Hi", options={})
        assert "source_repository" in str(excinfo.value)


def _mock_response(json_data: dict):
    resp = type("Res", (), {})()
    resp.status_code = 200
    resp.json = lambda: json_data
    resp.raise_for_status = lambda: None
    return resp


def cursor_handler__should_return_last_assistant_message__when_agent_finishes() -> None:
    with patch.dict("os.environ", {"CURSOR_API_KEY": "key_test"}):
        handler = CursorHandler()
        get_responses = [
            _mock_response({"status": "FINISHED"}),
            _mock_response(
                {
                    "messages": [
                        {"type": "assistant_message", "text": "Let me look at the code..."},
                        {"type": "assistant_message", "text": '{"summary": "Done"}'},
                    ]
                }
            ),
        ]
        get_iter = iter(get_responses)

        with patch("offie.handlers.ai.cursor.httpx.Client") as client_cls, patch("builtins.print"):
            enter = client_cls.return_value.__enter__.return_value
            enter.post.return_value = _mock_response({"id": "bc_123", "status": "CREATING"})
            enter.get.side_effect = lambda *a, **k: next(get_iter)
            result = handler.generate(
                prompt="Do something",
                options={"source_repository": "https://github.com/org/repo"},
            )

    assert result == '{"summary": "Done"}'


def cursor_handler__should_print_assistant_messages__when_log_level_is_info() -> None:
    with patch.dict("os.environ", {"CURSOR_API_KEY": "key_test"}):
        handler = CursorHandler()
        get_responses = [
            _mock_response({"status": "FINISHED"}),
            _mock_response(
                {
                    "messages": [
                        {"type": "assistant_message", "text": "Agent reply here"},
                    ]
                }
            ),
        ]
        get_iter = iter(get_responses)

        with (
            patch("offie.handlers.ai.cursor.httpx.Client") as client_cls,
            patch("builtins.print") as print_mock,
        ):
            enter = client_cls.return_value.__enter__.return_value
            enter.post.return_value = _mock_response({"id": "agent_1", "status": "CREATING"})
            enter.get.side_effect = lambda *a, **k: next(get_iter)
            handler.generate(
                prompt="Hi",
                options={"source_repository": "https://github.com/org/repo"},
                log_level="info",
            )

    printed = [call.args[0] for call in print_mock.call_args_list if call.args]
    assert any("[Cursor] Message" in p and "Agent reply here" in p for p in printed)


def cursor_handler__should_not_print_assistant_messages__when_log_level_is_warning() -> None:
    with patch.dict("os.environ", {"CURSOR_API_KEY": "key_test"}):
        handler = CursorHandler()
        get_responses = [
            _mock_response({"status": "FINISHED"}),
            _mock_response(
                {
                    "messages": [
                        {"type": "assistant_message", "text": "Should not appear"},
                    ]
                }
            ),
        ]
        get_iter = iter(get_responses)

        with (
            patch("offie.handlers.ai.cursor.httpx.Client") as client_cls,
            patch("builtins.print") as print_mock,
        ):
            enter = client_cls.return_value.__enter__.return_value
            enter.post.return_value = _mock_response({"id": "agent_1", "status": "CREATING"})
            enter.get.side_effect = lambda *a, **k: next(get_iter)
            result = handler.generate(
                prompt="Hi",
                options={"source_repository": "https://github.com/org/repo"},
                log_level="warning",
            )

    assert result == "Should not appear"
    printed = [call.args[0] for call in print_mock.call_args_list if call.args]
    assert not any("[Cursor] Message" in p and "Should not appear" in p for p in printed)
