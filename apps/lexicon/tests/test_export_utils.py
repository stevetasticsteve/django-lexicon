import os
import shutil
import tempfile

import pytest
from django.http import HttpRequest

from apps.lexicon.utils import export


@pytest.fixture
def temp_export_folder(monkeypatch):
    """Temporarily override the export_folder for tests."""
    temp_dir = tempfile.mkdtemp()
    monkeypatch.setattr(export, "export_folder", temp_dir)
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def dummy_project(english_project):
    # Add a version and affix_file for export
    english_project.version = 1
    english_project.affix_file = "SFX sample"
    english_project.save()
    return english_project


@pytest.fixture
def dummy_request():
    req = HttpRequest()
    req.META["SERVER_NAME"] = "testserver"
    req.META["SERVER_PORT"] = "80"
    req.path = "/"
    req.get_host = lambda: "testserver"
    req.build_absolute_uri = lambda url=None: f"http://testserver{url or '/'}"
    return req


def test_sanitize_filename_component():
    assert export.sanitize_filename_component("en/../g") == "en____g"
    assert export.sanitize_filename_component("en*bad?name") == "en_bad_name"
    assert export.sanitize_filename_component("en_good-name") == "en_good-name"


def test_check_export_folder_creates_and_checks(temp_export_folder):
    # Should not raise
    export.check_export_folder()
    # Should be a directory and writable
    assert os.path.isdir(export.export_folder)
    assert os.access(export.export_folder, os.W_OK)


@pytest.mark.django_db
def test_create_dic_file_creates_file(temp_export_folder, dummy_project, english_words):
    path = export.create_dic_file(dummy_project, checked=False)
    assert os.path.exists(path)
    with open(path) as f:
        lines = f.read().splitlines()
        # First line is count, then words
        assert lines[0] == str(len(english_words))
        assert "test_word" in lines[1:]
        assert "extra_word" in lines[1:]


@pytest.mark.django_db
def test_create_xml_file_creates_file(temp_export_folder, dummy_project, english_words):
    path = export.create_xml_file(dummy_project, checked=False)
    assert os.path.exists(path)
    with open(path) as f:
        content = f.read()
        assert '<?xml version="1.0"' in content
        assert '<Status Word="test_word"' in content
        assert '<Status Word="extra_word"' in content


@pytest.mark.django_db
def test_export_entries_dispatches_correct_format(
    monkeypatch, dummy_project, dummy_request
):
    called = {}
    monkeypatch.setattr(
        export,
        "create_dic_file",
        lambda *a, **kw: called.setdefault("dic", True) or "dicfile",
    )
    monkeypatch.setattr(
        export,
        "create_oxt_package",
        lambda *a, **kw: called.setdefault("oxt", True) or "oxtfile",
    )
    monkeypatch.setattr(
        export,
        "create_xml_file",
        lambda *a, **kw: called.setdefault("xml", True) or "xmlfile",
    )
    # Should call dic
    export.export_entries("dic", dummy_project, False, dummy_request)
    assert "dic" in called
    # Should call oxt
    export.export_entries("oxt", dummy_project, False, dummy_request)
    assert "oxt" in called
    # Should call xml
    export.export_entries("xml", dummy_project, False, dummy_request)
    assert "xml" in called


@pytest.mark.django_db
def test_create_oxt_package_creates_zip(
    temp_export_folder, dummy_project, english_words, dummy_request, monkeypatch
):
    path = export.create_oxt_package(
        dummy_project, checked=False, request=dummy_request
    )
    assert os.path.exists(path)
    from zipfile import ZipFile

    with ZipFile(path) as z:
        files = z.namelist()
        assert any(f.endswith(".dic") for f in files)
        assert any(f.endswith(".aff") for f in files)
        assert "dictionaries.xcu" in files
        assert "description.xml" in files
        assert "License.txt" in files
        assert "META-INF/manifest.xml" in files
