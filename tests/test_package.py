from importlib.metadata import version

import prism


def test_module_version_matches_package_metadata():
    """The invariant that survives a bump.

    Pinning a literal here means every version bump breaks the gate that
    authorises the release — and inside release.yaml, which runs the suite
    after the tag is already published.
    """
    assert prism.__version__ == version("prism-svg")
