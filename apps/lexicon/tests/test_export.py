import os
import shutil
import tempfile

import pytest
from django.http import HttpRequest
from django.urls import reverse

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
    """Test dangerous filenames are sanitized correctly."""
    assert export._sanitize_filename_component("en/../g") == "en____g"
    assert export._sanitize_filename_component("en*bad?name") == "en_bad_name"
    assert export._sanitize_filename_component("en_good-name") == "en_good-name"


def test_check_export_folder_creates_and_checks(temp_export_folder):
    """Test that the export folder is created and checked."""
    # Should not raise
    export._check_export_folder()
    # Should be a directory and writable
    assert os.path.isdir(export.export_folder)
    assert os.access(export.export_folder, os.W_OK)


@pytest.mark.django_db
def test_create_dic_file_creates_file(temp_export_folder, dummy_project, english_words):
    path = export._create_dic_file(dummy_project, checked=False)
    assert os.path.exists(path)
    with open(path) as f:
        lines = f.read().splitlines()
        # First line is count, then words
        assert lines[0] == str(len(english_words))
        assert "test_word" in lines[1:]
        assert "extra_word" in lines[1:]


@pytest.mark.django_db
def test_create_xml_file_creates_file(temp_export_folder, dummy_project, english_words):
    """Test that XML file is created with correct content."""
    path = export._create_xml_file(dummy_project, checked=False)
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
    """Test that export_entries calls the correct functions based on format."""
    called = {}
    monkeypatch.setattr(
        export,
        "_create_dic_file",
        lambda *a, **kw: called.setdefault("dic", True) or "dicfile",
    )
    monkeypatch.setattr(
        export,
        "_create_oxt_package",
        lambda *a, **kw: called.setdefault("oxt", True) or "oxtfile",
    )
    monkeypatch.setattr(
        export,
        "_create_xml_file",
        lambda *a, **kw: called.setdefault("xml", True) or "xmlfile",
    )
    # Should call dic
    export.export_entries(
        "dic", dummy_project, dummy_request, checked=False, hunspell=False
    )
    assert "dic" in called
    # Should call oxt
    export.export_entries(
        "oxt", dummy_project, dummy_request, checked=False, hunspell=False
    )
    assert "oxt" in called
    # Should call xml
    export.export_entries(
        "xml", dummy_project, dummy_request, checked=False, hunspell=False
    )
    assert "xml" in called


@pytest.mark.django_db
def test_create_oxt_package_creates_zip(
    temp_export_folder, dummy_project, english_words, dummy_request, monkeypatch
):
    """Test that OXT package is created with all required files."""
    path = export._create_oxt_package(
        dummy_project,
        request=dummy_request,
        checked=False,
        hunspell=False,
        ignore_word_flag=False,
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


@pytest.mark.django_db
class TestDicCreate:
    """Test the creation of the dic string with different configurations."""

    def test_dic_oxt_create_string_hunspell(self, project_with_affix_file):
        """Test that the dic string is created with hunspell conjugations."""

        # 1 test that hunspell conjugations are included with affix if hunspell is True
        string = export._create_dic_oxt_string(
            project_with_affix_file, checked=False, hunspell=True
        )
        assert "hobol/A" in string
        assert "\n\n" not in string  # No blank lines

        # 2 test that hunspell conjugations are included without affix if hunspell is False
        string = export._create_dic_oxt_string(
            project_with_affix_file, checked=False, hunspell=False
        )
        assert "hobol/A" not in string
        assert "hobol" in string
        assert "\n\n" not in string  # No blank lines

    def test_dic_oxt_create_string_checked(self, project_with_affix_file):
        """Test that the dic string is created with hunspell conjugations."""

        # 1 test that checked words are included when checked is True
        string = export._create_dic_oxt_string(
            project_with_affix_file, checked=True, hunspell=False
        )
        assert "checked_word" in string
        assert "hobol" not in string
        assert "\n\n" not in string  # No blank lines

        # 2 test that unchecked words are included when checked is False
        string = export._create_dic_oxt_string(
            project_with_affix_file, checked=False, hunspell=False
        )
        assert "checked_word" in string
        assert "hobol" in string
        assert "\n\n" not in string  # No blank lines

    def test_dic_oxt_create_string_ignore(self, project_with_affix_file):
        """Test that the dic string is created with hunspell conjugations."""

        # 1 test that ignore words are included with affix if hunspell is True
        string = export._create_dic_oxt_string(
            project_with_affix_file, checked=True, hunspell=True, ignore_word_flag=True
        )
        assert "ignoreme/!" in string
        assert "\n\n" not in string  # No blank lines

        # 2 test that ignore words are included without affix if hunspell is False
        string = export._create_dic_oxt_string(
            project_with_affix_file, checked=True, hunspell=False, ignore_word_flag=True
        )
        assert "ignoreme" in string
        assert "/!" not in string
        assert "\n\n" not in string  # No blank lines

        # 3 test that ignore words are not included if ignore_words is False
        string = export._create_dic_oxt_string(
            project_with_affix_file,
            checked=True,
            hunspell=False,
            ignore_word_flag=False,
        )
        assert "ignoreme" not in string
        assert "/!" not in string
        assert "\n\n" not in string  # No blank lines

    def test_dic_create_string_hunspell(self, project_with_affix_file):
        """Test that the plain dic string is created with checked words only."""
        # 1 test that hunspell conjugations are included with affix if hunspell is True
        string = export._create_dic_string(
            project_with_affix_file,
            checked=False,
            hunspell=True,
            ignore_word_flag=False,
        )
        assert "checked_word" in string
        assert "hobolyam" in string
        assert "/A" not in string
        assert "\n\n" not in string  # No blank lines

        # 2 test that hunspell conjugations are included without affix if hunspell is False
        string = export._create_dic_string(
            project_with_affix_file,
            checked=False,
            hunspell=False,
            ignore_word_flag=False,
        )
        assert "checked_word" in string
        assert "hobol" in string
        assert "hobolyam" not in string
        assert "/A" not in string
        assert "\n\n" not in string  # No blank lines

    def test_dic_create_string_checked(self, project_with_affix_file):
        """Test that the plain dic string is created with checked words only."""
        # 1 test that checked words are included when checked is True
        string = export._create_dic_string(
            project_with_affix_file,
            checked=True,
            hunspell=False,
            ignore_word_flag=False,
        )
        assert "checked_word" in string
        assert "hobol" not in string
        assert "/A" not in string
        assert "\n\n" not in string  # No blank lines

        # 2 test that unchecked words are included when checked is False
        string = export._create_dic_string(
            project_with_affix_file,
            checked=False,
            hunspell=False,
            ignore_word_flag=False,
        )
        assert "checked_word" in string
        assert "hobol" in string
        assert "/A" not in string
        assert "\n\n" not in string  # No blank lines

    def test_dic_create_string_ignore(self, project_with_affix_file):
        """Test that the plain dic string is created with checked words only."""
        # 1 test that ignore words are included when ignore_words is True
        string = export._create_dic_string(
            project_with_affix_file,
            checked=False,
            ignore_word_flag=True,
            hunspell=False,
        )
        assert "ignoreme" in string
        assert "/A" not in string
        assert "/!" not in string
        assert "\n\n" not in string  # No blank lines

        # 2 test that ignore words are not included when ignore_words is False
        string = export._create_dic_string(
            project_with_affix_file,
            checked=False,
            ignore_word_flag=False,
            hunspell=False,
        )
        assert "ignoreme" not in string
        assert "/A" not in string
        assert "/!" not in string
        assert "\n\n" not in string  # No blank lines


@pytest.mark.django_db
class TestXmlCreate:
    def test_xml_create_string_format(self, project_with_affix_file):
        """Test that the xml string is formatted correctly."""
        string = export._create_xml_string(
            project_with_affix_file,
            checked=False,
            hunspell=True,
            ignore_word_flag=True,
        )
        assert string.startswith('<?xml version="1.0" encoding="utf-8"?>')
        assert string.endswith("</SpellingStatus>")

    def test_xml_create_string_hunspell(self, project_with_affix_file):
        """Test that the xml string is created with different configurations."""
        # 1 test that hunspell conjugations are included with affix if hunspell is True
        string = export._create_xml_string(
            project_with_affix_file,
            checked=False,
            hunspell=True,
            ignore_word_flag=False,
        )
        assert '<Status Word="hobol" State="R" />' in string
        assert '<Status Word="hobolyam" State="R" />' in string
        assert "/A" not in string
        assert "\n\n" not in string

        # 2 test that hunspell conjugations are included without affix if hunspell is False
        string = export._create_xml_string(
            project_with_affix_file,
            checked=False,
            hunspell=False,
            ignore_word_flag=False,
        )
        assert '<Status Word="hobol" State="R" />' in string
        assert '<Status Word="hobolyam" State="R" />' not in string
        assert "/A" not in string
        assert "\n\n" not in string

    def test_xml_create_string_checked(self, project_with_affix_file):
        """Test that the xml string is created with different configurations."""
        # 1 test that checked conjugations are included if checked is True
        string = export._create_xml_string(
            project_with_affix_file,
            checked=True,
            hunspell=True,
            ignore_word_flag=False,
        )
        assert '<Status Word="checked_word" State="R" />' in string
        assert '<Status Word="hobol" State="R" />' not in string
        assert "/A" not in string
        assert "\n\n" not in string

        # 2 test that unchecked conjugations are included if checked is False
        string = export._create_xml_string(
            project_with_affix_file,
            checked=False,
            hunspell=False,
            ignore_word_flag=False,
        )
        assert '<Status Word="checked_word" State="R" />' in string
        assert '<Status Word="hobol" State="R" />' in string
        assert "/A" not in string
        assert "\n\n" not in string

    def test_xml_create_string_ignore(self, project_with_affix_file):
        """Test that the xml string is created with different configurations."""
        # 1 test that ignore words are included if ignore_flag is True
        string = export._create_xml_string(
            project_with_affix_file,
            checked=False,
            hunspell=False,
            ignore_word_flag=True,
        )
        assert '<Status Word="ignoreme" State="R" />' in string
        assert '<Status Word="hobol" State="R" />' in string
        assert "/A" not in string
        assert "\n\n" not in string

        # 2 test that ignore words are not included if ignore_flag is False
        string = export._create_xml_string(
            project_with_affix_file,
            checked=False,
            hunspell=False,
            ignore_word_flag=False,
        )
        assert '<Status Word="ignoreme" State="R" />' not in string
        assert '<Status Word="hobol" State="R" />' in string
        assert "/A" not in string
        assert "\n\n" not in string


@pytest.mark.django_db
class TestExportView:
    def test_export_view_get(self, client, project_with_affix_file):
        response = client.get(
            reverse(
                "lexicon:export_page",
                kwargs={"lang_code": project_with_affix_file.language_code},
            )
        )
        assert response.status_code == 200

    def test_export_view_post_oxt(self, client, project_with_affix_file):
        """Test that posting to the export view returns an OXT file."""
        response = client.post(
            reverse(
                "lexicon:export_page",
                kwargs={"lang_code": project_with_affix_file.language_code},
            ),
            data={
                "export_type": "oxt",
                "include_hunspell": True,
                "include_ignore": True,
            },
        )
        assert response.status_code == 200
        assert response.has_header("Content-Disposition")
        assert response["Content-Disposition"].startswith("attachment;")
        assert response["Content-Disposition"].endswith('.oxt"')

    def test_export_view_post_dic(self, client, project_with_affix_file):
        """Test that posting to the export view returns an OXT file."""
        response = client.post(
            reverse(
                "lexicon:export_page",
                kwargs={"lang_code": project_with_affix_file.language_code},
            ),
            data={
                "export_type": "dic",
                "include_hunspell": True,
                "include_ignore": True,
            },
        )
        assert response.status_code == 200
        assert response.has_header("Content-Disposition")
        assert response["Content-Disposition"].startswith("attachment;")
        assert response["Content-Disposition"].endswith('.dic"')
