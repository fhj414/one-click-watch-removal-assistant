from __future__ import annotations

import uuid
from typing import Any

from app.core.config import TEMPLATE_DIR
from app.core.storage import now_iso, read_json, write_json


TEMPLATE_INDEX = TEMPLATE_DIR / "templates.json"


def list_templates() -> list[dict[str, Any]]:
    return read_json(TEMPLATE_INDEX, [])


def create_template(payload: dict[str, Any]) -> dict[str, Any]:
    templates = list_templates()
    now = now_iso()
    record = {
        "id": str(uuid.uuid4()),
        "name": payload["name"],
        "mapping": payload["mapping"],
        "source_columns": payload.get("source_columns", []),
        "created_at": now,
        "updated_at": now,
    }
    templates.insert(0, record)
    write_json(TEMPLATE_INDEX, templates[:100])
    return record
