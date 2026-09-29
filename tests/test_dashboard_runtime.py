from datetime import datetime, timezone
import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


@pytest.mark.parametrize("failed_only", [False, True])
def test_dashboard_handles_empty_or_failed_only_window(monkeypatch, tmp_path, failed_only):
    log = tmp_path / "logs.jsonl"
    now = datetime.now(timezone.utc).isoformat()
    rows = []
    if failed_only:
        rows = [
            {"ts": now, "event": "request_received"},
            {"ts": now, "event": "request_failed", "tool_success": False,
             "tool_name": "retrieval", "error_type": "RuntimeError"},
        ]
    log.write_text("\n".join(json.dumps(row) for row in rows))
    monkeypatch.setenv("DASHBOARD_LOG_PATH", str(log))
    app = AppTest.from_file(str(Path(__file__).parents[1] / "scripts/dashboard.py"))
    app.run(timeout=20)
    assert not app.exception
    assert app.metric[0].value == ("1" if failed_only else "0")
