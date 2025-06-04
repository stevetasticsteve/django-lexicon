import pytest
import subprocess

from apps.lexicon.utils import hunspell


def test_check_length_dic_contents_inserts_length():
    """Test that check_length_dic_contents inserts a length header if missing."""
    # No header
    content = "word1\nword2"
    result = hunspell.check_length_dic_contents(content, default_length=42)
    lines = result.splitlines()
    assert lines[0] == "42"
    assert "word1" in lines
    assert "word2" in lines


def test_check_length_dic_contents_keeps_existing_length():
    """Test that check_length_dic_contents keeps existing length header."""
    content = "2\nword1\nword2"
    result = hunspell.check_length_dic_contents(content, default_length=99)
    lines = result.splitlines()
    assert lines[0] == "2"
    assert "word1" in lines
    assert "word2" in lines


def test_check_length_dic_contents_empty():
    """Test that check_length_dic_contents handles empty content."""
    content = ""
    result = hunspell.check_length_dic_contents(content, default_length=7)
    lines = result.splitlines()
    assert lines[0] == "7"


def test_unmunch_success(monkeypatch):
    """Test that unmunch processes words correctly."""
    # Mock subprocess.run to simulate unmunch output
    class DummyResult:
        def __init__(self):
            self.stdout = "walked\nwalking"
            self.stderr = ""

        def check_returncode(self):
            pass

    monkeypatch.setattr("subprocess.run", lambda *a, **kw: DummyResult())
    out = hunspell.unmunch("2\nwalk", "SFX")
    assert out == ["walked", "walking"]


def test_unmunch_failure(monkeypatch):
    """Test that unmunch raises an error on failure."""
    # Mock subprocess.run to simulate a failure
    class DummyResult:
        def __init__(self):
            self.stdout = ""
            self.stderr = "error"

        def check_returncode(self):
            raise subprocess.CalledProcessError(1, "unmunch", output="", stderr="error")

    monkeypatch.setattr("subprocess.run", lambda *a, **kw: DummyResult())
    with pytest.raises(RuntimeError) as excinfo:
        hunspell.unmunch("2\nwalk", "SFX")
    assert "unmunch failed: error" in str(excinfo.value)
