"""Tests for the chiptune CLI."""

from __future__ import annotations

import json


class TestCLI:
    def test_list_json_all(self, capsys) -> None:
        from chiptune.cli import main

        exit_code = main(["list", "--json"])
        assert exit_code == 0

        stdout = capsys.readouterr().out.strip()
        payload = json.loads(stdout)

        assert payload["program"] == "chiptune"
        assert payload["schema"] == 1
        assert isinstance(payload["version"], str)
        assert "presets" in payload
        assert "effects" in payload
        assert "sfx" in payload
        assert any(item["name"] == "battle" for item in payload["presets"])
        assert any(item["name"] == "retro" for item in payload["effects"])
        assert any(item["name"] == "coin" for item in payload["sfx"])

    def test_list_json_presets_only(self, capsys) -> None:
        from chiptune.cli import main

        exit_code = main(["list", "--json", "presets"])
        assert exit_code == 0

        stdout = capsys.readouterr().out.strip()
        payload = json.loads(stdout)

        assert "presets" in payload
        assert "effects" not in payload
        assert "sfx" not in payload

    def test_version_flag(self, capsys) -> None:
        from chiptune.cli import main

        exit_code = main(["--version"])
        assert exit_code == 0

        stdout = capsys.readouterr().out.strip()
        assert stdout.startswith("chiptune ")

    def test_format_output_conflict_errors(self, tmp_path, capsys) -> None:
        from chiptune.cli import main

        output_path = tmp_path / "conflict.mid"
        exit_code = main(["generate", "--format", "wav", "--output", str(output_path)])
        assert exit_code == 1

        stderr = capsys.readouterr().err
        assert "conflicts with --output extension" in stderr

    def test_generate_json_no_save(self, capsys) -> None:
        from chiptune.cli import main

        exit_code = main(["generate", "--json", "--format", "midi", "--no-save"])
        assert exit_code == 0

        stdout = capsys.readouterr().out.strip()
        payload = json.loads(stdout)
        assert payload["program"] == "chiptune"
        assert payload["schema"] == 1
        assert payload["command"] == "generate"
        assert payload["format"] == "midi"
        assert payload["saved"] is False
        assert payload["output"] is None
        assert payload["artifact"] is None
        assert isinstance(payload["seed"], int)

    def test_sfx_format_conflict_errors(self, tmp_path, capsys) -> None:
        from chiptune.cli import main

        output_path = tmp_path / "coin.mid"
        exit_code = main(["sfx", "coin", "--format", "wav", "--output", str(output_path)])
        assert exit_code == 1

        stderr = capsys.readouterr().err
        assert "conflicts with --output extension" in stderr

    def test_completion_bash(self, capsys) -> None:
        from chiptune.cli import main

        exit_code = main(["completion", "bash"])
        assert exit_code == 0

        stdout = capsys.readouterr().out
        assert "complete -F _chiptune_complete chiptune" in stdout

    def test_generate_metadata_file(self, tmp_path) -> None:
        from chiptune.cli import main

        metadata_path = tmp_path / "gen.json"
        exit_code = main(
            ["generate", "--format", "midi", "--no-save", "--metadata", str(metadata_path)]
        )
        assert exit_code == 0
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        assert payload["command"] == "generate"
        assert payload["saved"] is False
        assert payload["artifact"] is None

    def test_sfx_metadata_file(self, tmp_path) -> None:
        from chiptune.cli import main

        metadata_path = tmp_path / "sfx.json"
        exit_code = main(
            ["sfx", "coin", "--format", "midi", "--no-save", "--metadata", str(metadata_path)]
        )
        assert exit_code == 0
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        assert payload["command"] == "sfx"
        assert payload["saved"] is False
        assert payload["artifact"] is None

    def test_sfx_json_no_save(self, capsys) -> None:
        from chiptune.cli import main

        exit_code = main(["sfx", "coin", "--json", "--format", "midi", "--no-save"])
        assert exit_code == 0

        stdout = capsys.readouterr().out.strip()
        payload = json.loads(stdout)
        assert payload["command"] == "sfx"
        assert payload["saved"] is False
        assert payload["output"] is None
        assert payload["artifact"] is None
