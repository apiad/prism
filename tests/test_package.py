import prism


def test_package_exposes_version():
    assert isinstance(prism.__version__, str)
    assert prism.__version__ == "0.1.0"
