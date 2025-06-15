import re
from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.utils import IntegrityError
from django.urls import reverse

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


@pytest.mark.django_db
class TestLexiconEntryModel:
    """Tests for the models.LexiconEntry model."""

    # --- Fixtures for specific test scenarios ---
    @pytest.fixture
    def project_with_validator(self, db):
        """A project with a tok_ples_validator allowing only lowercase letters."""
        return models.LexiconProject.objects.create(
            language_name="Validated Language",
            language_code="vld",
            tok_ples_validator="^[a-z]+$",
        )

    @pytest.fixture
    def project_with_invalid_regex_validator(self, db):
        """A project with an invalid regex for tok_ples_validator."""
        return models.LexiconProject.objects.create(
            language_name="Invalid Regex Lang",
            language_code="irl",
            tok_ples_validator="[",  # Invalid regex pattern
        )

    # --- Basic Creation and Field Tests ---

    def test_create_valid_entry(self, english_project):
        """Test creating an entry with all valid required fields."""
        entry = models.LexiconEntry.objects.create(
            project=english_project,
            tok_ples="testword",
            eng="testgloss",
        )
        assert entry.pk is not None
        assert entry.project == english_project
        assert entry.tok_ples == "testword"  # Should be lowercased by save()
        assert entry.eng == "testgloss"  # Should be lowercased by save()
        assert entry.review == "0"
        assert entry.checked is False
        assert entry.created == date.today()
        assert entry.modified == date.today()

    def test_tok_ples_lowercase_on_save(self, english_project):
        """tok_ples should be lowercased on save."""
        entry = models.LexiconEntry.objects.create(
            project=english_project, tok_ples="TestWord", eng="Gloss"
        )
        assert entry.tok_ples == "testword"

    def test_eng_lowercase_on_save(self, english_project):
        """eng should be lowercased on save."""
        entry = models.LexiconEntry.objects.create(
            project=english_project, tok_ples="word", eng="GlosS"
        )
        assert entry.eng == "gloss"

    def test_oth_lang_lowercase_on_save(self, english_project):
        """oth_lang should be lowercased on save if present."""
        entry = models.LexiconEntry.objects.create(
            project=english_project, tok_ples="word", eng="gloss", oth_lang="OTHer"
        )
        assert entry.oth_lang == "other"

        entry_no_oth_lang = models.LexiconEntry.objects.create(
            project=english_project, tok_ples="word2", eng="gloss2"
        )
        assert entry_no_oth_lang.oth_lang is None

    # --- Required Field Validation ---

    def test_project_required(self):
        """Project should be a required field."""
        with pytest.raises(ValidationError) as excinfo:
            entry = models.LexiconEntry(tok_ples="missingproject", eng="missing")
            entry.full_clean()
        assert "project" in excinfo.value.message_dict

    def test_tok_ples_required(self, english_project):
        """tok_ples should be a required field."""
        with pytest.raises(ValidationError) as excinfo:
            entry = models.LexiconEntry(project=english_project, eng="missing")
            entry.full_clean()
        assert "tok_ples" in excinfo.value.message_dict

    def test_eng_required(self, english_project):
        """eng should be a required field (blank=False, null=True implies this is a form requirement)."""
        # Note: If eng is meant to be truly optional in the DB (can be NULL),
        # it should be blank=True, null=True. Current def is blank=False, null=True,
        # which means it's required in forms but can be NULL in DB if not set.
        # full_clean() should catch it because of blank=False.
        with pytest.raises(ValidationError) as excinfo:
            entry = models.LexiconEntry(project=english_project, tok_ples="missingeng")
            entry.full_clean()
        assert "eng" in excinfo.value.message_dict

    # --- Max Length Tests ---

    def test_tok_ples_max_length(self, english_project):
        """Test tok_ples respects max_length."""
        with pytest.raises(ValidationError) as excinfo:
            entry = models.LexiconEntry(
                project=english_project,
                tok_ples="a" * 61,  # Exceeds max_length=60
                eng="gloss",
            )
            entry.full_clean()
        assert "tok_ples" in excinfo.value.message_dict
        assert (
            "Ensure this value has at most 60 characters"
            in excinfo.value.message_dict["tok_ples"][0]
        )

    def test_eng_max_length(self, english_project):
        """Test eng respects max_length."""
        with pytest.raises(ValidationError) as excinfo:
            entry = models.LexiconEntry(
                project=english_project,
                tok_ples="word",
                eng="a" * 61,  # Exceeds max_length=60
            )
            entry.full_clean()
        assert "eng" in excinfo.value.message_dict
        assert (
            "Ensure this value has at most 60 characters"
            in excinfo.value.message_dict["eng"][0]
        )

    def test_oth_lang_max_length(self, english_project):
        """Test oth_lang respects max_length."""
        with pytest.raises(ValidationError) as excinfo:
            entry = models.LexiconEntry(
                project=english_project,
                tok_ples="word",
                eng="gloss",
                oth_lang="a" * 61,  # Exceeds max_length=60
            )
            entry.full_clean()
        assert "oth_lang" in excinfo.value.message_dict
        assert (
            "Ensure this value has at most 60 characters"
            in excinfo.value.message_dict["oth_lang"][0]
        )

    def test_review_user_max_length(self, english_project):
        """Test review_user respects max_length."""
        with pytest.raises(ValidationError) as excinfo:
            entry = models.LexiconEntry(
                project=english_project,
                tok_ples="word",
                eng="gloss",
                review_user="a" * 46,  # Exceeds max_length=45
            )
            entry.full_clean()
        assert "review_user" in excinfo.value.message_dict
        assert (
            "Ensure this value has at most 45 characters"
            in excinfo.value.message_dict["review_user"][0]
        )

    def test_modified_by_max_length(self, english_project):
        """Test modified_by respects max_length."""
        with pytest.raises(ValidationError) as excinfo:
            entry = models.LexiconEntry(
                project=english_project,
                tok_ples="word",
                eng="gloss",
                modified_by="a" * 46,  # Exceeds max_length=45
            )
            entry.full_clean()
        assert "modified_by" in excinfo.value.message_dict
        assert (
            "Ensure this value has at most 45 characters"
            in excinfo.value.message_dict["modified_by"][0]
        )

    # --- Choices and Default Tests ---

    def test_review_choices(self, english_project):
        """Test review field respects choices."""
        entry_valid = models.LexiconEntry.objects.create(
            project=english_project, tok_ples="valid", eng="valid", review="1"
        )
        assert entry_valid.review == "1"

        with pytest.raises(ValidationError) as excinfo:
            entry_invalid = models.LexiconEntry(
                project=english_project,
                tok_ples="invalid",
                eng="invalid",
                review="9",  # Invalid choice
            )
            entry_invalid.full_clean()
        assert "review" in excinfo.value.message_dict
        assert "'9' is not a valid choice" in excinfo.value.message_dict["review"][0]

    def test_pos_choices(self, english_project):
        """Test pos field respects choices."""
        entry_valid = models.LexiconEntry.objects.create(
            project=english_project, tok_ples="valid", eng="valid", pos="n"
        )
        assert entry_valid.pos == "n"

        with pytest.raises(ValidationError) as excinfo:
            entry_invalid = models.LexiconEntry(
                project=english_project,
                tok_ples="invalid",
                eng="invalid",
                pos="xyz",  # Invalid choice
            )
            entry_invalid.full_clean()
        assert "pos" in excinfo.value.message_dict
        assert "'xyz' is not a valid choice" in excinfo.value.message_dict["pos"][0]

    def test_review_default(self, english_project):
        """Review should default to '0'."""
        entry = models.LexiconEntry.objects.create(
            project=english_project, tok_ples="defaultrev", eng="defaultgloss"
        )
        assert entry.review == "0"

    def test_checked_default(self, english_project):
        """Checked should default to False."""
        entry = models.LexiconEntry.objects.create(
            project=english_project, tok_ples="defaultchecked", eng="defaultgloss"
        )
        assert entry.checked is False

    # --- Relationships ---

    def test_project_foreign_key_deletion(self, english_project):
        """Deleting a project should cascade delete its entries."""
        entry = models.LexiconEntry.objects.create(
            project=english_project, tok_ples="todelete", eng="todelete"
        )
        pk = entry.pk
        english_project.delete()
        assert not models.LexiconEntry.objects.filter(pk=pk).exists()

    def test_paradigms_many_to_many(self, english_project, english_words_with_paradigm):
        """Test ManyToManyField relationship with Paradigm."""
        entry = models.LexiconEntry.objects.create(
            project=english_project, tok_ples="verb", eng="to act"
        )
        assert entry.paradigms.count() == 0

        words, paradigm, conjugation = english_words_with_paradigm
        entry.paradigms.add(paradigm)
        assert entry.paradigms.count() == 1
        assert paradigm in entry.paradigms.all()

        # Test adding another paradigm
        paradigm2 = models.Paradigm.objects.create(
            name="Test Paradigm2",
            row_labels=["row1"],
            column_labels=["col1"],
            project=english_project,
        )
        entry.paradigms.add(paradigm2)
        assert entry.paradigms.count() == 2
        assert paradigm2 in entry.paradigms.all()

    # --- Method Tests (`__str__`, `get_absolute_url`) ---

    def test_str_method(self, english_project):
        """Test the __str__ method output."""
        entry = models.LexiconEntry.objects.create(
            project=english_project, tok_ples="hello", eng="greeting"
        )
        assert str(entry) == f"Word: hello in {english_project.language_name}"

    def test_get_absolute_url_method(self, english_project):
        """Test the get_absolute_url method output."""
        entry = models.LexiconEntry.objects.create(
            project=english_project, tok_ples="page", eng="webpage"
        )
        expected_url = reverse(
            "lexicon:entry_detail", args=(english_project.language_code, entry.pk)
        )
        assert entry.get_absolute_url() == expected_url

    # --- `clean()` Method Tests ---

    def test_clean_no_project_validator(self, english_project):
        """clean() should pass if project has no tok_ples_validator."""
        # english_project doesn't have a validator by default
        entry = models.LexiconEntry(
            project=english_project, tok_ples="anycharacters123", eng="any"
        )
        entry.full_clean()  # Should not raise ValidationError

    def test_clean_with_valid_tok_ples(self, project_with_validator):
        """clean() should pass if tok_ples matches project's validator."""
        entry = models.LexiconEntry(
            project=project_with_validator, tok_ples="validword", eng="ok"
        )
        entry.full_clean()  # Should not raise ValidationError

    def test_clean_with_invalid_tok_ples(self, project_with_validator):
        """clean() should raise ValidationError if tok_ples doesn't match project's validator."""
        with pytest.raises(ValidationError) as excinfo:
            entry = models.LexiconEntry(
                project=project_with_validator, tok_ples="Invalid Word 123", eng="fail"
            )
            # The save() method lowercases, so we must test with the post-lowercased value
            # or ensure clean() is called before save(). `full_clean()` is correct here.
            entry.full_clean()
        assert "Tok ples" in excinfo.value.message_dict["__all__"][0]
        assert (
            "Tok ples 'invalid word 123' contains unallowed characters. A project admin set this restriction."
            in excinfo.value.message_dict["__all__"][0]
        )

    def test_clean_with_invalid_project_regex(
        self, project_with_invalid_regex_validator
    ):
        """clean() should raise ValidationError if project's tok_ples_validator is invalid."""
        with pytest.raises(ValidationError) as excinfo:
            entry = models.LexiconEntry(
                project=project_with_invalid_regex_validator,
                tok_ples="test",
                eng="test",
            )
            entry.full_clean()
        assert "Tok ples" in excinfo.value.message_dict["__all__"][0]
        assert "Invalid regex pattern" in excinfo.value.message_dict["__all__"][0]

    # --- `save()` Method Tests (Version Increment, Timestamps) ---

    def test_version_not_incremented_on_new_entry(self, english_project):
        """Project version should not increment on initial entry creation."""
        initial_version = english_project.version
        models.LexiconEntry.objects.create(
            project=english_project, tok_ples="newentry", eng="new"
        )
        english_project.refresh_from_db()  # Refresh project to get latest version
        assert english_project.version == initial_version

    def test_version_incremented_on_tok_ples_change(self, english_project):
        """Project version should increment when tok_ples is changed."""
        entry = models.LexiconEntry.objects.create(
            project=english_project, tok_ples="original", eng="original"
        )
        initial_version = english_project.version

        entry.tok_ples = "changed"
        entry.save()  # Call save()
        english_project.refresh_from_db()

        assert english_project.version == initial_version + 1
        assert entry.tok_ples == "changed"  # Verify change took effect

    def test_version_not_incremented_on_other_field_change(self, english_project):
        """Project version should not increment when other fields are changed."""
        entry = models.LexiconEntry.objects.create(
            project=english_project, tok_ples="stable", eng="original"
        )
        initial_version = english_project.version

        entry.eng = "updated"  # Change only 'eng'
        entry.save()
        english_project.refresh_from_db()

        assert english_project.version == initial_version
        assert entry.eng == "updated"

    def test_created_and_modified_timestamps(self, english_project):
        """created should be set on creation, modified updated on changes."""
        entry = models.LexiconEntry.objects.create(
            project=english_project, tok_ples="timecheck", eng="timecheck"
        )
        assert entry.created == date.today()
        assert entry.modified == date.today()

        # Simulate time passing (e.g., a day later) for modified
        # In real tests, you might use freezegun or mock datetime.now()
        # For this test, we'll just check if it gets updated
        import time

        time.sleep(0.01)  # Ensure a slight time difference for `auto_now`
        entry.eng = "updatedgloss"
        entry.save()
        entry.refresh_from_db()  # Get latest timestamps

        assert entry.created == date.today()  # created should not change
        assert entry.modified >= entry.created  # modified should be same or later
        # It's hard to test 'later' precisely without mocking time, but this ensures it's not earlier.

    # --- Constraints Tests ---
    def test_unique_tok_ples_per_project_constraint(self, english_project):
        """tok_ples must be unique within the same project (case-insensitive due to save() lowercasing)."""
        models.LexiconEntry.objects.create(
            project=english_project, tok_ples="unique", eng="unique"
        )

        # Attempt to create another entry with same tok_ples in the same project
        entry = models.LexiconEntry(
            project=english_project,
            tok_ples="Unique",
            eng="duplicate",  # Different case
        )
        with pytest.raises(ValidationError):
            entry.full_clean()  # Call full_clean first to ensure validation is hit
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                entry.save()  # Then save, which will trigger the unique constraint at DB level if full_clean passes

        # Also test with exact same case (will still fail due to save() lowercasing)
        entry = models.LexiconEntry(
            project=english_project, tok_ples="unique", eng="duplicate_same_case"
        )
        # The 2nd word should fail validation as Unique -> unique in save
        with pytest.raises(ValidationError):
            entry.full_clean()
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                entry.save()  # This save will also fail due to unique constraint

    def test_tok_ples_not_unique_across_projects(self, english_project, kovol_project):
        """tok_ples does not need to be unique across different projects."""
        models.LexiconEntry.objects.create(
            project=english_project, tok_ples="hello", eng="greeting"
        )
        # Should be able to create "hello" in a different project
        entry_in_other_project = models.LexiconEntry.objects.create(
            project=kovol_project, tok_ples="hello", eng="gud de"
        )
        assert entry_in_other_project.pk is not None  # Successfully created
        assert (
            models.LexiconEntry.objects.filter(tok_ples="hello").count() == 2
        )  # Two entries with "hello"


@pytest.mark.django_db
class TestParadigmModel:
    def test_row_and_column_labels_must_be_lists(self, english_project):
        # Valid case
        paradigm = models.Paradigm(
            name="Valid",
            project=english_project,
            part_of_speech="n",
            row_labels=["row1", "row2"],
            column_labels=["col1", "col2"],
        )
        paradigm.full_clean()  # Should not raise

        # Invalid row_labels
        paradigm.row_labels = "notalist"
        with pytest.raises(ValidationError):
            paradigm.full_clean()

        # Invalid column_labels
        paradigm.row_labels = ["row1"]
        paradigm.column_labels = "notalist"
        with pytest.raises(ValidationError):
            paradigm.full_clean()

    def test_unique_name_per_project(self, english_project):
        models.Paradigm.objects.create(
            name="UniqueName",
            project=english_project,
            part_of_speech="n",
            row_labels=["row1"],
            column_labels=["col1"],
        )
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                models.Paradigm.objects.create(
                    name="UniqueName",
                    project=english_project,
                    part_of_speech="n",
                    row_labels=["row2"],
                    column_labels=["col2"],
                )


@pytest.mark.django_db
class TestConjugationModel:
    def test_conjugation_lowercase_and_regex(self, english_project):
        # Set up a regex that only allows lowercase letters
        english_project.tok_ples_validator = r"[a-z]+"
        english_project.save()
        word = models.LexiconEntry.objects.create(
            tok_ples="word", eng="gloss", project=english_project
        )
        paradigm = models.Paradigm.objects.create(
            name="Test",
            project=english_project,
            part_of_speech="n",
            row_labels=["row1"],
            column_labels=["col1"],
        )
        # Valid conjugation
        conj = models.Conjugation(
            word=word, paradigm=paradigm, row=0, column=0, conjugation="valid"
        )
        conj.full_clean()  # Should not raise
        conj.save()
        assert conj.conjugation == "valid"

        # Invalid conjugation (contains a digit)
        conj2 = models.Conjugation(
            word=word, paradigm=paradigm, row=0, column=0, conjugation="bad1"
        )
        with pytest.raises(ValidationError):
            conj2.full_clean()

        # Uppercase should be normalized to lowercase on save
        conj3 = models.Conjugation(
            word=word, paradigm=paradigm, row=0, column=1, conjugation="UPPER"
        )
        # conj3.full_clean()
        conj3.save()
        assert conj3.conjugation == "upper"

    def test_unique_conjugation_position(self, english_project):
        word = models.LexiconEntry.objects.create(
            tok_ples="word", eng="gloss", project=english_project
        )
        paradigm = models.Paradigm.objects.create(
            name="Test2",
            project=english_project,
            part_of_speech="n",
            row_labels=["row1"],
            column_labels=["col1"],
        )
        models.Conjugation.objects.create(
            word=word, paradigm=paradigm, row=0, column=0, conjugation="a"
        )
        # Same position should fail
        with pytest.raises(ValidationError):
            with transaction.atomic():
                models.Conjugation.objects.create(
                    word=word, paradigm=paradigm, row=0, column=0, conjugation="b"
                )
        # Different position should succeed
        models.Conjugation.objects.create(
            word=word, paradigm=paradigm, row=0, column=1, conjugation="c"
        )


@pytest.mark.django_db
class TestVariationModel:
    def test_create_variation(self, english_project):
        word = models.LexiconEntry.objects.create(
            project=english_project, tok_ples="word", eng="gloss"
        )
        variation = models.Variation.objects.create(
            word=word,
            type="spelling",
            text="spellingvar",
            included_in_spellcheck=True,
            included_in_search=True,
            notes="A note",
        )
        assert variation.pk is not None
        assert variation.word == word
        assert variation.type == "spelling"
        assert variation.text == "spellingvar"
        assert variation.included_in_spellcheck is True
        assert variation.included_in_search is True
        assert variation.notes == "A note"

    def test_str_method(self, english_project):
        word = models.LexiconEntry.objects.create(
            project=english_project, tok_ples="word", eng="gloss"
        )
        variation = models.Variation.objects.create(
            word=word, type="dialect", text="dialectvar"
        )
        s = str(variation)
        assert "Variation for: 'Word: word in English'" in s
        assert "dialectvar" in s
        assert "Dialectal Variant" in s

    def test_type_choices(self, english_project):
        word = models.LexiconEntry.objects.create(
            project=english_project, tok_ples="word", eng="gloss"
        )
        # Valid type
        models.Variation.objects.create(word=word, type="spelling", text="ok")
        # Invalid type
        with pytest.raises(ValidationError):
            v = models.Variation(word=word, type="notatype", text="fail")
            v.full_clean()

    def test_text_required_and_max_length(self, english_project):
        word = models.LexiconEntry.objects.create(
            project=english_project, tok_ples="word", eng="gloss"
        )
        # Required
        with pytest.raises(ValidationError):
            v = models.Variation(word=word, type="spelling", text=None)
            v.full_clean()
        # Max length
        with pytest.raises(ValidationError):
            v = models.Variation(word=word, type="spelling", text="a" * 101)
            v.full_clean()

    def test_get_absolute_url(self, english_project):
        word = models.LexiconEntry.objects.create(
            project=english_project, tok_ples="word", eng="gloss"
        )
        variation = models.Variation.objects.create(
            word=word, type="spelling", text="spellingvar"
        )
        url = variation.get_absolute_url()
        assert str(word.pk) in url
        assert word.project.language_code in url
