import json
from pathlib import Path

from codex_thread_bridge.bridge import register_thread_owner


def test_owner_registration_follows_launcher_ancestors(monkeypatch, tmp_path):
    worker = tmp_path / "worker"
    sessions = tmp_path / ".claude/sessions"
    sessions.mkdir(parents=True)
    (sessions / "200.json").write_text(json.dumps({"sessionId": "owner-session"}))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("CODEX_HOME", str(worker))
    monkeypatch.setattr("os.getpid", lambda: 100)

    def parent(command, **kwargs):
        assert command == ["ps", "-o", "ppid=", "-p", "100"]
        return "200\n"

    monkeypatch.setattr("subprocess.check_output", parent)
    register_thread_owner("worker-thread")
    assert (worker / "claude-notify/worker-thread").read_text() == "owner-session\n"
    assert not (tmp_path / ".codex").exists()


def test_non_claude_launch_does_not_register_an_owner(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "worker"))
    monkeypatch.setattr("os.getpid", lambda: 100)
    monkeypatch.setattr("subprocess.check_output", lambda *args, **kwargs: "1\n")
    register_thread_owner("worker-thread")
    assert not (tmp_path / "worker").exists()


def test_invalid_claude_metadata_does_not_block_dispatch(monkeypatch, tmp_path):
    sessions = tmp_path / ".claude/sessions"
    sessions.mkdir(parents=True)
    (sessions / "100.json").write_text("not JSON")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "worker"))
    monkeypatch.setattr("os.getpid", lambda: 100)
    register_thread_owner("worker-thread")
    assert not (tmp_path / "worker").exists()
