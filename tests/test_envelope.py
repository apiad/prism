import pytest

from prism.envelope import Envelope, load_spec
from prism.errors import SpecError


def test_load_spec_reads_yaml_text():
    data = load_spec("type: flow\nsteps: [{label: A}]\n")
    assert data["type"] == "flow"


def test_load_spec_reads_a_file(tmp_path):
    path = tmp_path / "d.yaml"
    path.write_text("type: flow\nsteps: [{label: A}]\n")
    assert load_spec(path)["type"] == "flow"


def test_spec_without_type_is_rejected():
    with pytest.raises(SpecError):
        load_spec("steps: [{label: A}]\n")


def test_non_mapping_spec_is_rejected():
    with pytest.raises(SpecError):
        load_spec("- just\n- a list\n")


def test_malformed_yaml_is_rejected():
    with pytest.raises(SpecError):
        load_spec("type: flow\n  bad: [indent\n")


def test_envelope_defaults():
    env = Envelope(type="flow")
    assert env.theme == "default"
    assert env.width == 900
    assert env.tokens == {}


def test_envelope_ignores_archetype_payload_keys():
    env = Envelope.model_validate({"type": "flow", "steps": [{"label": "A"}]})
    assert env.type == "flow"
