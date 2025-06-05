import re

import pytest
from django.core.exceptions import ValidationError

from apps.lexicon import models


@pytest.mark.django_db
class TestLexiconProjectModel:
    """Tests for the LexiconProject model."""

    def test_create_valid_project(self):
        """Test creating a project with all valid required fields."""
        project = models.LexiconProject.objects.create(
            language_name="Test Language",
            language_code="tst",
        )
        assert project.pk is not None
        assert project.language_name == "Test Language"
        assert project.language_code == "tst"
        assert project.version == 0  # Default value
        assert project.secondary_language is None
        assert project.tok_ples_validator is None
        assert project.affix_file.startswith(
            "# Hunspell affix file for Kovol by NTMPNG"
        )  # Check default affix file

    def test_language_name_required(self):
        """language_name should be required."""
        with pytest.raises(ValidationError) as excinfo:
            project = models.LexiconProject(language_code="req")
            project.full_clean()  # Call full_clean to trigger model validation
        assert "language_name" in excinfo.value.message_dict

    def test_language_code_required(self):
        """language_code should be required."""
        with pytest.raises(ValidationError) as excinfo:
            project = models.LexiconProject(language_name="Required Lang")
            project.full_clean()
        assert "language_code" in excinfo.value.message_dict

    def test_language_code_unique(self):
        """language_code should be unique."""
        models.LexiconProject.objects.create(
            language_name="Lang One", language_code="lon"
        )
        with pytest.raises(ValidationError) as excinfo:
            project = models.LexiconProject(
                language_name="Lang Two", language_code="lon"
            )
            project.full_clean()  # Triggers unique constraint check
        assert "language_code" in excinfo.value.message_dict
        assert "already exists" in excinfo.value.message_dict["language_code"][0]

    def test_secondary_language_optional(self):
        """secondary_language should be optional and save correctly."""
        project = models.LexiconProject.objects.create(
            language_name="Optional Lang",
            language_code="opt",
            secondary_language="Tok Pisin",
        )
        assert project.secondary_language == "Tok Pisin"

        project_no_secondary = models.LexiconProject.objects.create(
            language_name="No Secondary", language_code="nsc"
        )
        assert project_no_secondary.secondary_language is None

    def test_version_default_value(self):
        """Version should default to 0."""
        project = models.LexiconProject.objects.create(
            language_name="Version Test", language_code="vrt"
        )
        assert project.version == 0

    def test_affix_file_default_value(self):
        """affix_file should have the correct default content."""
        project = models.LexiconProject.objects.create(
            language_name="Affix Test", language_code="aft"
        )
        assert project.affix_file.startswith(
            "# Hunspell affix file for Kovol by NTMPNG"
        )
        assert "NOSUGGEST !" in project.affix_file

    def test_tok_ples_validator_valid_regex(self):
        """tok_ples_validator should allow valid regex patterns."""
        valid_regex = r"^[a-zA-Z\s]+$"
        project = models.LexiconProject.objects.create(
            language_name="Regex Valid",
            language_code="rgv",
            tok_ples_validator=valid_regex,
        )
        assert project.tok_ples_validator == valid_regex
        # Ensure it can be compiled without error
        re.compile(project.tok_ples_validator)

    def test_tok_ples_validator_invalid_regex(self):
        """tok_ples_validator should raise ValidationError for invalid regex patterns."""
        invalid_regex = r"["  # Unclosed bracket
        with pytest.raises(ValidationError) as excinfo:
            project = models.LexiconProject(
                language_name="Regex Invalid",
                language_code="rgi",
                tok_ples_validator=invalid_regex,
            )
            project.full_clean()  # This triggers the clean() method with regex compilation
        assert "tok_ples_validator" in excinfo.value.message_dict
        assert (
            "This is not a valid regular expression."
            in excinfo.value.message_dict["tok_ples_validator"]
        )

    def test_tok_ples_validator_null_or_empty(self):
        """tok_ples_validator can be null or an empty string."""
        project_null_validator = models.LexiconProject.objects.create(
            language_name="Null Validator",
            language_code="nul",
            tok_ples_validator=None,
        )
        assert project_null_validator.tok_ples_validator is None

        project_empty_validator = models.LexiconProject.objects.create(
            language_name="Empty Validator",
            language_code="emp",
            tok_ples_validator="",
        )
        assert project_empty_validator.tok_ples_validator == ""

    def test_str_method(self):
        """The __str__ method should return the expected string."""
        project = models.LexiconProject.objects.create(
            language_name="String Test", language_code="str"
        )
        assert str(project) == "String Test lexicon project"

    def test_max_length_language_name(self):
        """Test max_length for language_name."""
        with pytest.raises(ValidationError) as excinfo:
            project = models.LexiconProject(language_name="a" * 46, language_code="max")
            project.full_clean()
        assert "language_name" in excinfo.value.message_dict
        assert (
            "Ensure this value has at most 45 characters"
            in excinfo.value.message_dict["language_name"][0]
        )

    def test_max_length_language_code(self):
        """Test max_length for language_code."""
        with pytest.raises(ValidationError) as excinfo:
            project = models.LexiconProject(
                language_name="Code Too Long", language_code="tools"
            )
            project.full_clean()
        assert "language_code" in excinfo.value.message_dict
        assert (
            "Ensure this value has at most 4 characters"
            in excinfo.value.message_dict["language_code"][0]
        )

    def test_max_length_secondary_language(self):
        """Test max_length for secondary_language."""
        with pytest.raises(ValidationError) as excinfo:
            project = models.LexiconProject(
                language_name="Secondary Too Long",
                language_code="stl",
                secondary_language="a" * 46,
            )
            project.full_clean()
        assert "secondary_language" in excinfo.value.message_dict
        assert (
            "Ensure this value has at most 45 characters"
            in excinfo.value.message_dict["secondary_language"][0]
        )

    def test_max_length_tok_ples_validator(self):
        """Test max_length for tok_ples_validator."""
        with pytest.raises(ValidationError) as excinfo:
            project = models.LexiconProject(
                language_name="Validator Too Long",
                language_code="vtl",
                tok_ples_validator="a" * 61,
            )
            project.full_clean()
        assert "tok_ples_validator" in excinfo.value.message_dict
        assert (
            "Ensure this value has at most 60 characters"
            in excinfo.value.message_dict["tok_ples_validator"][0]
        )
