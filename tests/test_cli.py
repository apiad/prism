import json

from prism.cli import main


def test_render_writes_output(tmp_path):
    out = tmp_path / "d.svg"
    assert main(["render", "examples/flow-ingestion.yaml", "-o", str(out)]) == 0
    assert out.read_text().startswith("<svg")


def test_render_to_stdout_when_no_output_given(capsys):
    assert main(["render", "examples/flow-ingestion.yaml"]) == 0
    assert capsys.readouterr().out.startswith("<svg")


def test_archetypes_lists_flow(capsys):
    assert main(["archetypes"]) == 0
    assert "flow" in capsys.readouterr().out


def test_themes_lists_default(capsys):
    assert main(["themes"]) == 0
    assert "default" in capsys.readouterr().out


def test_icons_lists_known_names(capsys):
    assert main(["icons"]) == 0
    assert "database" in capsys.readouterr().out


def test_schema_emits_json_schema(capsys):
    assert main(["schema", "flow"]) == 0
    schema = json.loads(capsys.readouterr().out)
    assert "steps" in schema["properties"]


def test_bad_spec_exits_nonzero_with_a_readable_message(tmp_path, capsys):
    bad = tmp_path / "bad.yaml"
    bad.write_text("type: flowchart\nsteps: [{label: A}]\n")
    assert main(["render", str(bad)]) == 1
    assert "flow" in capsys.readouterr().err
