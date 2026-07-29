from pathlib import Path

import pytest

from prism.cli import main
from prism.errors import PrismError
from prism.theme import load_theme, scaffold_theme


def test_scaffold_writes_a_file_named_after_the_theme(tmp_path):
    out = scaffold_theme("house", directory=tmp_path)
    assert out == tmp_path / "house.yaml"
    assert out.exists()


def test_scaffolded_theme_loads_and_carries_the_new_name(tmp_path):
    out = scaffold_theme("house", directory=tmp_path)
    theme = load_theme(str(out))
    assert theme.name == "house"


def test_scaffold_copies_the_requested_source(tmp_path):
    out = scaffold_theme("night", source="dark", directory=tmp_path)
    assert load_theme(str(out)).palette == load_theme("dark").palette


def test_scaffold_defaults_to_the_default_theme(tmp_path):
    out = scaffold_theme("house", directory=tmp_path)
    assert load_theme(str(out)).palette == load_theme("default").palette


def test_scaffold_explains_the_constraints_in_a_header(tmp_path):
    text = scaffold_theme("house", directory=tmp_path).read_text()
    assert text.startswith("#")
    assert "grotesque" in text
    assert "700" in text


def test_scaffold_refuses_to_clobber(tmp_path):
    scaffold_theme("house", directory=tmp_path)
    with pytest.raises(PrismError) as excinfo:
        scaffold_theme("house", directory=tmp_path)
    assert "--force" in str(excinfo.value)


def test_scaffold_overwrites_with_force(tmp_path):
    first = scaffold_theme("house", directory=tmp_path)
    first.write_text("clobbered")
    second = scaffold_theme("house", directory=tmp_path, force=True)
    assert load_theme(str(second)).name == "house"


def test_scaffold_rejects_an_unknown_source(tmp_path):
    with pytest.raises(PrismError) as excinfo:
        scaffold_theme("house", source="drak", directory=tmp_path)
    assert "dark" in str(excinfo.value)


def test_scaffold_accepts_an_explicit_path_and_creates_parents(tmp_path):
    target = tmp_path / "nested" / "brand.yaml"
    out = scaffold_theme("brand", out_path=target)
    assert out == target
    assert load_theme(str(out)).name == "brand"


def test_cli_new_theme_creates_the_file(tmp_path, capsys):
    target = tmp_path / "house.yaml"
    assert main(["new-theme", "house", "-o", str(target)]) == 0
    assert load_theme(str(target)).name == "house"
    assert "house.yaml" in capsys.readouterr().out


def test_cli_new_theme_honours_from(tmp_path):
    target = tmp_path / "night.yaml"
    assert main(["new-theme", "night", "--from", "dark", "-o", str(target)]) == 0
    assert load_theme(str(target)).palette == load_theme("dark").palette


def test_cli_new_theme_reports_a_bad_source(tmp_path, capsys):
    target = tmp_path / "x.yaml"
    assert main(["new-theme", "x", "--from", "drak", "-o", str(target)]) == 1
    assert "dark" in capsys.readouterr().err


def test_cli_new_theme_refuses_to_clobber(tmp_path, capsys):
    target = tmp_path / "house.yaml"
    assert main(["new-theme", "house", "-o", str(target)]) == 0
    assert main(["new-theme", "house", "-o", str(target)]) == 1
    assert "--force" in capsys.readouterr().err


def test_scaffolded_theme_actually_renders(tmp_path):
    import prism

    out = scaffold_theme("house", source="paper", directory=tmp_path)
    spec = f"type: flow\ntheme: {out}\nsteps: [{{label: Draft}}, {{label: Ship}}]\n"
    assert prism.render_str(spec).startswith("<svg")


def test_scaffold_rejects_a_name_that_is_not_a_filename(tmp_path):
    with pytest.raises(PrismError):
        scaffold_theme("../escape", directory=tmp_path)


def test_scaffold_directory_defaults_to_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    out = scaffold_theme("house")
    assert out.resolve().parent == Path(tmp_path).resolve()
