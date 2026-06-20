# Shared configuration types
from __future__ import annotations

import json
from typing import Annotated

from pydantic.functional_validators import BeforeValidator


def parse_json_list(value: object) -> list[str]:
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Cannot parse {value!r} into a list")


JsonList = Annotated[list[str], BeforeValidator(parse_json_list)]
