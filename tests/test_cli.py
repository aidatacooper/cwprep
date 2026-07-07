"""
cwprep CLI tests.
"""

import json

import pytest

from cwprep import __version__
from cwprep import cli


pytest.importorskip("mcp")


def _write_spec(path):
    path.write_text(
        json.dumps(
            {
                "flow_name": "CLI Test Flow",
                "connection": {
                    "host": "localhost",
                    "username": "root",
                    "dbname": "test_db",
                },
                "nodes": [
                    {"type": "input_sql", "name": "orders", "sql": "SELECT * FROM orders"},
                    {
                        "type": "output_server",
                        "name": "output",
                        "parent": "orders",
                        "datasource_name": "CLI_Output",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )


def test_version(capsys):
    with pytest.raises(SystemExit):
        cli.main(["--version"])
    out = capsys.readouterr().out
    assert f"cwprep {__version__}" in out


def test_no_args_tty_prints_help(monkeypatch, capsys):
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)
    assert cli.main([]) == 0
    out = capsys.readouterr().out
    assert "Smart entry" in out
    assert "cwprep" in out


def test_no_args_pipe_starts_mcp(monkeypatch):
    called = {}

    def fake_handle_mcp(args):
        called["transport"] = args.transport
        return 0

    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(cli, "_handle_mcp", fake_handle_mcp)
    assert cli.main([]) == 0
    assert called["transport"] == "stdio"


def test_env_cli_forces_help(monkeypatch, capsys):
    monkeypatch.setenv("CWPREP_MODE", "cli")
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: False)
    assert cli.main([]) == 0
    assert "Smart entry" in capsys.readouterr().out


def test_status_json(capsys):
    assert cli.main(["status", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["version"] == __version__
    assert payload["smart_entrypoint"] == "cwprep"


def test_capabilities_json(capsys):
    assert cli.main(["capabilities", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert any(op["type"] == "input_sql" for op in payload["operations"])


def test_validate_json(workspace_tmp_dir, capsys):
    spec = workspace_tmp_dir / "flow.json"
    _write_spec(spec)
    assert cli.main(["validate", str(spec), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"] is True


def test_run_dry_run(workspace_tmp_dir, capsys):
    spec = workspace_tmp_dir / "flow.json"
    _write_spec(spec)
    output = workspace_tmp_dir / "flow.tfl"
    assert cli.main(["run", str(spec), "--out", str(output), "--dry-run", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"] is True
    assert payload["node_count"] == 2
    assert not output.exists()


def test_run_generates_tfl(workspace_tmp_dir, capsys):
    spec = workspace_tmp_dir / "flow.json"
    _write_spec(spec)
    output = workspace_tmp_dir / "flow.tfl"
    assert cli.main(["run", str(spec), "--out", str(output), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert output.exists()


def test_run_refuses_existing_output_without_force(workspace_tmp_dir, capsys):
    spec = workspace_tmp_dir / "flow.json"
    _write_spec(spec)
    output = workspace_tmp_dir / "flow.tfl"
    output.write_text("existing", encoding="utf-8")
    assert cli.main(["run", str(spec), "--out", str(output)]) == 1
    assert "Output already exists" in capsys.readouterr().err


def test_translate_spec(workspace_tmp_dir, capsys):
    spec = workspace_tmp_dir / "flow.json"
    _write_spec(spec)
    assert cli.main(["translate", str(spec)]) == 0
    assert "WITH" in capsys.readouterr().out
