"""Simple JSON file persistence — no external database."""

from __future__ import annotations

import json
import os
import threading
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

_lock = threading.Lock()
_store: Optional["JsonStore"] = None

COLLECTIONS = (
    "users",
    "jobs",
    "candidates",
    "interviews",
    "interview_questions",
    "email_logs",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _data_dir() -> Path:
    raw = os.environ.get("DATA_DIR", "data")
    return Path(raw)


class JsonStore:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.store_path = self.data_dir / "store.json"
        self.resumes_dir = self.data_dir / "resumes"
        self.resumes_dir.mkdir(parents=True, exist_ok=True)
        if not self.store_path.exists():
            self._write(self._empty())

    def _empty(self) -> dict[str, list]:
        return {name: [] for name in COLLECTIONS}

    def _read(self) -> dict[str, list]:
        with self.store_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        for name in COLLECTIONS:
            data.setdefault(name, [])
        return data

    def _write(self, data: dict[str, list]) -> None:
        with self.store_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def _mutate(self, fn) -> Any:
        with _lock:
            data = self._read()
            result = fn(data)
            self._write(data)
            return result

    def counts(self) -> dict[str, int]:
        data = self._read()
        return {name: len(data.get(name, [])) for name in COLLECTIONS}

    def save_resume_file(self, filename: str, content: bytes) -> str:
        safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)
        path = self.resumes_dir / f"{uuid.uuid4()}_{safe}"
        path.write_bytes(content)
        return str(path)

    # --- users ---
    def find_user_by_email(self, email: str) -> Optional[dict]:
        email = email.strip().lower()
        for u in self._read()["users"]:
            if u.get("email", "").lower() == email:
                return deepcopy(u)
        return None

    def insert_user(self, email: str, password_hash: str, full_name: str) -> dict:
        def op(data):
            row = {
                "id": str(uuid.uuid4()),
                "email": email.strip(),
                "password_hash": password_hash,
                "full_name": full_name.strip(),
                "created_at": _now_iso(),
            }
            data["users"].append(row)
            return deepcopy(row)

        return self._mutate(op)

    # --- generic CRUD ---
    def list(
        self,
        collection: str,
        *,
        filters: Optional[dict] = None,
        order_by: Optional[str] = None,
        desc: bool = False,
        limit: Optional[int] = None,
    ) -> list[dict]:
        rows = deepcopy(self._read()[collection])
        if filters:
            for key, val in filters.items():
                rows = [r for r in rows if r.get(key) == val]
        if order_by:
            rows.sort(key=lambda r: r.get(order_by) or "", reverse=desc)
        if limit is not None:
            rows = rows[:limit]
        return rows

    def get(self, collection: str, record_id: str) -> Optional[dict]:
        for row in self._read()[collection]:
            if row.get("id") == record_id:
                return deepcopy(row)
        return None

    def insert(self, collection: str, record: dict) -> dict:
        def op(data):
            row = deepcopy(record)
            row.setdefault("id", str(uuid.uuid4()))
            row.setdefault("created_at", _now_iso())
            data[collection].append(row)
            return deepcopy(row)

        return self._mutate(op)

    def update(self, collection: str, record_id: str, patch: dict) -> Optional[dict]:
        def op(data):
            for i, row in enumerate(data[collection]):
                if row.get("id") == record_id:
                    row.update(patch)
                    data[collection][i] = row
                    return deepcopy(row)
            return None

        return self._mutate(op)

    def delete(self, collection: str, record_id: str) -> bool:
        def op(data):
            before = len(data[collection])
            data[collection] = [r for r in data[collection] if r.get("id") != record_id]
            return before != len(data[collection])

        return self._mutate(op)


def get_store() -> JsonStore:
    global _store
    if _store is None:
        _store = JsonStore(_data_dir())
    return _store
