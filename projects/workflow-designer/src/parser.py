"""YAML workflow parser with validation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


class WorkflowValidationError(Exception):
    """Raised when workflow validation fails."""
    pass


REQUIRED_WORKFLOW_FIELDS = {"name", "trigger", "steps"}
REQUIRED_TRIGGER_FIELDS = {"type"}
VALID_TRIGGER_TYPES = {"cron", "event", "manual"}
VALID_ACTION_TYPES = {"skill_call", "http_request", "notification", "delay", "condition", "script"}
REQUIRED_STEP_FIELDS = {"name", "action"}
VALID_SCHEDULE_PATTERN = re.compile(
    r"^([\d\*]+ ){4}[\d\*]+$"
)


class WorkflowParser:
    def __init__(self, workflows_dir: Path | str | None = None):
        self.workflows_dir = Path(workflows_dir) if workflows_dir else Path("workflows")

    def parse_file(self, path: Path | str) -> dict[str, Any]:
        path = Path(path)
        if not path.exists():
            raise WorkflowValidationError(f"File not found: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise WorkflowValidationError(f"YAML parse error in {path}: {e}")

        if data is None:
            raise WorkflowValidationError(f"Empty workflow file: {path}")

        self._validate(data, path)
        return data

    def parse_string(self, content: str) -> dict[str, Any]:
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise WorkflowValidationError(f"YAML parse error: {e}")

        if data is None:
            raise WorkflowValidationError("Empty workflow content")

        self._validate(data, "<string>")
        return data

    def _validate(self, data: dict[str, Any], source: str) -> None:
        missing = REQUIRED_WORKFLOW_FIELDS - set(data.keys())
        if missing:
            raise WorkflowValidationError(
                f"[{source}] Missing required fields: {missing}"
            )

        self._validate_trigger(data["trigger"], source)
        self._validate_steps(data["steps"], source)

    def _validate_trigger(self, trigger: Any, source: str) -> None:
        if not isinstance(trigger, dict):
            raise WorkflowValidationError(
                f"[{source}] 'trigger' must be a dictionary"
            )

        if "type" not in trigger:
            raise WorkflowValidationError(
                f"[{source}] trigger missing 'type' field"
            )

        ttype = trigger["type"]
        if ttype not in VALID_TRIGGER_TYPES:
            raise WorkflowValidationError(
                f"[{source}] Invalid trigger type '{ttype}'. "
                f"Must be one of: {VALID_TRIGGER_TYPES}"
            )

        if ttype == "cron":
            if "schedule" not in trigger:
                raise WorkflowValidationError(
                    f"[{source}] cron trigger missing 'schedule' field"
                )
            if not VALID_SCHEDULE_PATTERN.match(trigger["schedule"]):
                raise WorkflowValidationError(
                    f"[{source}] Invalid cron schedule format: "
                    f"'{trigger['schedule']}'. Expected: 'min hour dom mon dow'"
                )

        if ttype == "event":
            if "event_name" not in trigger:
                raise WorkflowValidationError(
                    f"[{source}] event trigger missing 'event_name' field"
                )

    def _validate_steps(self, steps: Any, source: str) -> None:
        if not isinstance(steps, list):
            raise WorkflowValidationError(
                f"[{source}] 'steps' must be a list"
            )

        if len(steps) == 0:
            raise WorkflowValidationError(
                f"[{source}] workflow must have at least one step"
            )

        step_names: set[str] = set()
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                raise WorkflowValidationError(
                    f"[{source}] Step {i} must be a dictionary"
                )

            missing = REQUIRED_STEP_FIELDS - set(step.keys())
            if missing:
                raise WorkflowValidationError(
                    f"[{source}] Step '{step.get('name', i)}' "
                    f"missing fields: {missing}"
                )

            name = step["name"]
            if name in step_names:
                raise WorkflowValidationError(
                    f"[{source}] Duplicate step name: '{name}'"
                )
            step_names.add(name)

            action = step["action"]
            if action not in VALID_ACTION_TYPES:
                raise WorkflowValidationError(
                    f"[{source}] Step '{name}': invalid action '{action}'. "
                    f"Must be one of: {VALID_ACTION_TYPES}"
                )

            if action == "skill_call":
                if "skill" not in step:
                    raise WorkflowValidationError(
                        f"[{source}] Step '{name}': skill_call requires 'skill' field"
                    )

            if action == "http_request":
                if "url" not in step:
                    raise WorkflowValidationError(
                        f"[{source}] Step '{name}': http_request requires 'url' field"
                    )

            if action == "delay":
                if "seconds" not in step:
                    raise WorkflowValidationError(
                        f"[{source}] Step '{name}': delay requires 'seconds' field"
                    )

            if action == "condition":
                if "expression" not in step:
                    raise WorkflowValidationError(
                        f"[{source}] Step '{name}': condition requires 'expression' field"
                    )

    def list_workflows(self) -> list[Path]:
        if not self.workflows_dir.exists():
            return []
        return sorted(self.workflows_dir.glob("*.yaml")) + sorted(self.workflows_dir.glob("*.yml"))

    def load_workflow(self, name: str) -> dict[str, Any]:
        candidates = [
            self.workflows_dir / f"{name}.yaml",
            self.workflows_dir / f"{name}.yml",
            Path(name),
        ]
        for path in candidates:
            if path.exists():
                return self.parse_file(path)

        raise WorkflowValidationError(
            f"Workflow '{name}' not found in {self.workflows_dir}"
        )
