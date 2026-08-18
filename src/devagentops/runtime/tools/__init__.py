from devagentops.runtime.tools._common import (
    MAX_TOOL_RESULT_BYTES,
    ExpectedToolError,
    ToolExecutionResult,
)
from devagentops.runtime.tools.find import execute_find
from devagentops.runtime.tools.grep import execute_grep
from devagentops.runtime.tools.ls import execute_ls
from devagentops.runtime.tools.read import execute_read
from devagentops.runtime.messages import JsonValue, ToolDefinition
from devagentops.runtime.workspace import RuntimeCaseWorkspace


TOOL_DEFINITIONS = (
    ToolDefinition(
        name="read",
        description=(
            "Read complete UTF-8 lines from /raw.log or a frozen /repository file. "
            "Offsets are 1-based and results are bounded with visible continuation."
        ),
        parameters={
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "path": {"type": "string", "minLength": 1},
                "offset": {"type": "integer", "minimum": 1},
                "limit": {"type": "integer", "minimum": 1, "maximum": 2000},
            },
            "required": ["path"],
        },
    ),
    ToolDefinition(
        name="grep",
        description=(
            "Search visible workspace text with a regex or literal pattern. "
            "Results distinguish matches from context and never re-apply .gitignore."
        ),
        parameters={
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "pattern": {"type": "string", "minLength": 1},
                "path": {"type": "string", "minLength": 1},
                "glob": {"type": "string", "minLength": 1},
                "ignore_case": {"type": "boolean"},
                "literal": {"type": "boolean"},
                "context": {"type": "integer", "minimum": 0},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100},
            },
            "required": ["pattern"],
        },
    ),
    ToolDefinition(
        name="find",
        description=(
            "Find paths by glob over the frozen visible workspace membership. "
            "Results are deterministic and do not re-apply .gitignore."
        ),
        parameters={
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "pattern": {"type": "string", "minLength": 1},
                "path": {"type": "string", "minLength": 1},
                "limit": {"type": "integer", "minimum": 1, "maximum": 1000},
            },
            "required": ["pattern"],
        },
    ),
    ToolDefinition(
        name="ls",
        description=(
            "List one directory level in deterministic alphabetical order, "
            "including dotfiles and marking directories with a trailing slash."
        ),
        parameters={
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "path": {"type": "string", "minLength": 1},
                "limit": {"type": "integer", "minimum": 1, "maximum": 500},
            },
            "required": [],
        },
    ),
)


def execute_tool(
    workspace: RuntimeCaseWorkspace,
    name: str,
    arguments: dict[str, JsonValue],
) -> ToolExecutionResult:
    definition = next((item for item in TOOL_DEFINITIONS if item.name == name), None)
    if definition is None:
        raise ExpectedToolError(f"unknown or disallowed tool: {name}", code="unknown_tool")
    _validate_arguments(definition, arguments)
    if name == "read":
        return execute_read(workspace, **arguments)
    if name == "grep":
        return execute_grep(workspace, **arguments)
    if name == "find":
        return execute_find(workspace, **arguments)
    return execute_ls(workspace, **arguments)


def _validate_arguments(
    definition: ToolDefinition,
    arguments: dict[str, JsonValue],
) -> None:
    if not isinstance(arguments, dict):
        raise ExpectedToolError("tool arguments must be an object", code="schema_invalid_arguments")
    schema = definition.parameters
    properties = schema["properties"]
    unknown = set(arguments) - set(properties)
    missing = set(schema["required"]) - set(arguments)
    if unknown or missing:
        detail = (
            f"unknown field {sorted(unknown)[0]!r}"
            if unknown
            else f"missing required field {sorted(missing)[0]!r}"
        )
        raise ExpectedToolError(detail, code="schema_invalid_arguments")
    for key, value in arguments.items():
        field = properties[key]
        expected = field["type"]
        valid = (
            isinstance(value, str)
            if expected == "string"
            else isinstance(value, bool)
            if expected == "boolean"
            else isinstance(value, int) and not isinstance(value, bool)
        )
        if not valid:
            raise ExpectedToolError(
                f"field {key!r} must have type {expected}",
                code="schema_invalid_arguments",
            )
        if expected in {"string", "integer"}:
            if "minLength" in field and len(value) < field["minLength"]:
                raise ExpectedToolError(
                    f"field {key!r} is too short", code="schema_invalid_arguments"
                )
            if "minimum" in field and value < field["minimum"]:
                raise ExpectedToolError(
                    f"field {key!r} is below its minimum", code="schema_invalid_arguments"
                )
            if "maximum" in field and value > field["maximum"]:
                raise ExpectedToolError(
                    f"field {key!r} exceeds its maximum", code="schema_invalid_arguments"
                )

__all__ = [
    "MAX_TOOL_RESULT_BYTES",
    "ExpectedToolError",
    "ToolExecutionResult",
    "TOOL_DEFINITIONS",
    "execute_tool",
    "execute_find",
    "execute_grep",
    "execute_ls",
    "execute_read",
]
