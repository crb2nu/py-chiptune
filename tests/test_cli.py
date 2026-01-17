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
