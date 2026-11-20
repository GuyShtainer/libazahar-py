"""examples/gym_env.py imports without gymnasium and refuses to build with the plain install line."""
import importlib.util
import sys
from pathlib import Path

import pytest

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "gym_env.py"


def load_example(monkeypatch):
    """Import the example with gymnasium made unimportable (a None entry in sys.modules blocks the import)."""
    monkeypatch.setattr(sys, "dont_write_bytecode", True)     # no examples/__pycache__: docs_check reads every file there
    for name in ("gymnasium", "gymnasium.spaces"):
        monkeypatch.setitem(sys.modules, name, None)
    spec = importlib.util.spec_from_file_location("gym_env_example", EXAMPLE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_import_without_gymnasium_then_clear_error(monkeypatch, tmp_path):
    module = load_example(monkeypatch)
    assert module.gymnasium is None
    with pytest.raises(ImportError, match="pip install gymnasium"):
        module.TestAppEnv("nothing.3dsx", tmp_path)
