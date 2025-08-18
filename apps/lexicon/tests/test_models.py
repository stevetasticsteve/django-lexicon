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
        assert project.text_validator is None
        assert project.affix_file.startswith(
            "# Hunspell affix file for LANGUAGE by NTMPNG"
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
            "# Hunspell affix file for LANGUAGE by NTMPNG"
        )
        assert "NOSUGGEST !" in project.affix_file

    def test_text_validator_valid_regex(self):
        """text_validator should allow valid regex patterns."""
        valid_regex = r"^[a-zA-Z\s]+$"
        project = models.LexiconProject.objects.create(
            language_name="Regex Valid",
            language_code="rgv",
            text_validator=valid_regex,
        )
        assert project.text_validator == valid_regex
        # Ensure it can be compiled without error
        re.compile(project.text_validator)

    def test_text_validator_invalid_regex(self):
        """text_validator should raise ValidationError for invalid regex patterns."""
        invalid_regex = r"["  # Unclosed bracket
        with pytest.raises(ValidationError) as excinfo:
            project = models.LexiconProject(
                language_name="Regex Invalid",
                language_code="rgi",
                text_validator=invalid_regex,
            )
            project.full_clean()  # This triggers the clean() method with regex compilation
        assert "text_validator" in excinfo.value.message_dict
        assert (
            "This is not a valid regular expression."
            in excinfo.value.message_dict["text_validator"]
        )

    def test_text_validator_null_or_empty(self):
        """text_validator can be null or an empty string."""
        project_null_validator = models.LexiconProject.objects.create(
            language_name="Null Validator",
            language_code="nul",
            text_validator=None,
        )
        assert project_null_validator.text_validator is None

        project_empty_validator = models.LexiconProject.objects.create(
            language_name="Empty Validator",
            language_code="emp",
            text_validator="",
        )
        assert project_empty_validator.text_validator == ""

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

    def test_max_length_text_validator(self):
        """Test max_length for text_validator."""
        with pytest.raises(ValidationError) as excinfo:
            project = models.LexiconProject(
                language_name="Validator Too Long",
                language_code="vtl",
                text_validator="a" * 61,
            )
            project.full_clean()
        assert "text_validator" in excinfo.value.message_dict
        assert (
            "Ensure this value has at most 60 characters"
            in excinfo.value.message_dict["text_validator"][0]
        )


@pytest.mark.django_db
class TestLexiconEntryModel:
    """Tests for the models.LexiconEntry model."""

    # --- Fixtures for specific test scenarios ---
    @pytest.fixture
    def project_with_validator(self, db):
        """A project with a text_validator allowing only lowercase letters."""
        return models.LexiconProject.objects.create(
            language_name="Validated Language",
            language_code="vld",
            text_validator="^[a-z]+$",
        )

    @pytest.fixture
    def project_with_invalid_regex_validator(self, db):
        """A project with an invalid regex for text_validator."""
        return models.LexiconProject.objects.create(
            language_name="Invalid Regex Lang",
            language_code="irl",
            text_validator="[",  # Invalid regex pattern
        )

    # --- Basic Creation and Field Tests ---

    def test_create_valid_entry(self, english_project):
        """Test creating an entry with all valid required fields."""
        entry = models.LexiconEntry.objects.create(
            project=english_project,
            text="testword",
        )
        assert entry.pk is not None
        assert entry.project == english_project
        assert entry.text == "testword"  # Should be lowercased by save()
        assert entry.review == "0"
        assert entry.checked is False
        assert entry.created == date.today()
        assert entry.modified == date.today()

    def test_text_lowercase_on_save(self, english_project):
        """text should be lowercased on save."""
        entry = models.LexiconEntry.objects.create(
            project=english_project, text="TestWord"
        )
        assert entry.text == "testword"

    # --- Required Field Validation ---

    def test_project_required(self):
        """Project should be a required field."""
        with pytest.raises(ValidationError) as excinfo:
            entry = models.LexiconEntry(text="missingproject")
            entry.full_clean()
        assert "project" in excinfo.value.message_dict

    def test_text_required(self, english_project):
        """text should be a required field."""
        with pytest.raises(ValidationError) as excinfo:
            entry = models.LexiconEntry(project=english_project)
            entry.full_clean()
        assert "text" in excinfo.value.message_dict

    # --- Max Length Tests ---

    def test_text_max_length(self, english_project):
        """Test text respects max_length."""
        with pytest.raises(ValidationError) as excinfo:
            entry = models.LexiconEntry(
                project=english_project,
                text="a" * 61,  # Exceeds max_length=60
            )
            entry.full_clean()
        assert "text" in excinfo.value.message_dict
        assert (
            "Ensure this value has at most 60 characters"
            in excinfo.value.message_dict["text"][0]
        )

    def test_review_user_max_length(self, english_project):
        """Test review_user respects max_length."""
        with pytest.raises(ValidationError) as excinfo:
            entry = models.LexiconEntry(
                project=english_project,
                text="word",
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
                text="word",
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
            project=english_project, text="valid", review="1"
        )
        assert entry_valid.review == "1"
        with pytest.raises(ValidationError) as excinfo:
            entry_invalid = models.LexiconEntry(
                project=english_project,
                text="invalid",
                review="9",  # Invalid choice
            )
            entry_invalid.full_clean()
        assert "review" in excinfo.value.message_dict
        assert "'9' is not a valid choice" in excinfo.value.message_dict["review"][0]

    def test_pos_choices(self, english_project):
        """Test pos field respects choices."""
        entry_valid = models.LexiconEntry.objects.create(
            project=english_project, text="valid", pos="n"
        )
        assert entry_valid.pos == "n"

        with pytest.raises(ValidationError) as excinfo:
            entry_invalid = models.LexiconEntry(
                project=english_project,
                text="invalid",
                pos="xyz",  # Invalid choice
            )
            entry_invalid.full_clean()
        assert "pos" in excinfo.value.message_dict
        assert "'xyz' is not a valid choice" in excinfo.value.message_dict["pos"][0]

    def test_review_default(self, english_project):
        """Review should default to '0'."""
        entry = models.LexiconEntry.objects.create(
            project=english_project, text="defaultrev"
        )
        assert entry.review == "0"

    def test_checked_default(self, english_project):
        """Checked should default to False."""
        entry = models.LexiconEntry.objects.create(
            project=english_project, text="defaultchecked"
        )
        assert entry.checked is False

    # --- Relationships ---

    def test_project_foreign_key_deletion(self, english_project):
        """Deleting a project should cascade delete its entries."""
        entry = models.LexiconEntry.objects.create(
            project=english_project, text="todelete"
        )
        pk = entry.pk
        english_project.delete()
        assert not models.LexiconEntry.objects.filter(pk=pk).exists()

    def test_paradigms_many_to_many(self, english_project, english_words_with_paradigm):
        """Test ManyToManyField relationship with Paradigm."""
        entry = models.LexiconEntry.objects.create(project=english_project, text="verb")
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
            project=english_project, text="hello"
        )
        assert str(entry) == f"Word: hello in {english_project.language_name}"

    def test_get_absolute_url_method(self, english_project):
        """Test the get_absolute_url method output."""
        entry = models.LexiconEntry.objects.create(project=english_project, text="page")
        expected_url = reverse(
            "lexicon:entry_detail", args=(english_project.language_code, entry.pk)
        )
        assert entry.get_absolute_url() == expected_url

    # --- `clean()` Method Tests ---

    def test_clean_no_project_validator(self, english_project):
        """clean() should pass if project has no text_validator."""
        # english_project doesn't have a validator by default
        entry = models.LexiconEntry(project=english_project, text="anycharacters123")
        entry.full_clean()  # Should not raise ValidationError

    def test_clean_with_valid_text(self, project_with_validator):
        """clean() should pass if text matches project's validator."""
        entry = models.LexiconEntry(project=project_with_validator, text="validword")
        entry.full_clean()  # Should not raise ValidationError

    def test_clean_with_invalid_text(self, project_with_validator):
        """clean() should raise ValidationError if text doesn't match project's validator."""
        with pytest.raises(ValidationError) as excinfo:
            entry = models.LexiconEntry(
                project=project_with_validator, text="Invalid Word 123"
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
        """clean() should raise ValidationError if project's text_validator is invalid."""
        with pytest.raises(ValidationError) as excinfo:
            entry = models.LexiconEntry(
                project=project_with_invalid_regex_validator,
                text="test",
            )
            entry.full_clean()
        assert "Tok ples" in excinfo.value.message_dict["__all__"][0]
        assert "Invalid regex pattern" in excinfo.value.message_dict["__all__"][0]

    # --- `save()` Method Tests (Version Increment, Timestamps) ---

    def test_version_not_incremented_on_new_entry(self, english_project):
        """Project version should not increment on initial entry creation."""
        initial_version = english_project.version
        models.LexiconEntry.objects.create(project=english_project, text="newentry")
        english_project.refresh_from_db()  # Refresh project to get latest version
        assert english_project.version == initial_version

    def test_version_incremented_on_text_change(self, english_project):
        """Project version should increment when text is changed."""
        entry = models.LexiconEntry.objects.create(
            project=english_project, text="original"
        )
        initial_version = english_project.version

        entry.text = "changed"
        entry.save()  # Call save()
        english_project.refresh_from_db()

        assert english_project.version == initial_version + 1
        assert entry.text == "changed"  # Verify change took effect

    def test_version_not_incremented_on_other_field_change(self, english_project):
        """Project version should not increment when other fields are changed."""
        entry = models.LexiconEntry.objects.create(
            project=english_project, text="stable"
        )
        initial_version = english_project.version
        entry.save()
        english_project.refresh_from_db()
        assert english_project.version == initial_version

    def test_created_and_modified_timestamps(self, english_project):
        """created should be set on creation, modified updated on changes."""
        entry = models.LexiconEntry.objects.create(
            project=english_project, text="timecheck"
        )
        assert entry.created == date.today()
        assert entry.modified == date.today()

        # Simulate time passing (e.g., a day later) for modified
        # In real tests, you might use freezegun or mock datetime.now()
        # For this test, we'll just check if it gets updated
        import time

        time.sleep(0.01)  # Ensure a slight time difference for `auto_now`
        entry.save()
        entry.refresh_from_db()  # Get latest timestamps

        assert entry.created == date.today()  # created should not change
        assert entry.modified >= entry.created  # modified should be same or later
        # It's hard to test 'later' precisely without mocking time, but this ensures it's not earlier.

    # --- Constraints Tests ---
    def test_unique_text_per_project_constraint(self, english_project):
        """text must be unique within the same project (case-insensitive due to save() lowercasing)."""
        models.LexiconEntry.objects.create(project=english_project, text="unique")

        # Attempt to create another entry with same text in the same project
        entry = models.LexiconEntry(
            project=english_project,
            text="Unique",
            # Different case
        )
        with pytest.raises(ValidationError):
            entry.full_clean()  # Call full_clean first to ensure validation is hit
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                entry.save()  # Then save, which will trigger the unique constraint at DB level if full_clean passes

        # Also test with exact same case (will still fail due to save() lowercasing)
        entry = models.LexiconEntry(project=english_project, text="unique")
        # The 2nd word should fail validation as Unique -> unique in save
        with pytest.raises(ValidationError):
            entry.full_clean()
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                entry.save()  # This save will also fail due to unique constraint

    def test_text_not_unique_across_projects(self, english_project, kovol_project):
        """text does not need to be unique across different projects."""
        models.LexiconEntry.objects.create(project=english_project, text="hello")
        # Should be able to create "hello" in a different project
        entry_in_other_project = models.LexiconEntry.objects.create(
            project=kovol_project, text="hello"
        )
        assert entry_in_other_project.pk is not None  # Successfully created
        assert (
            models.LexiconEntry.objects.filter(text="hello").count() == 2
        )  # Two entries with "hello"


@pytest.mark.django_db
class TestSenseModel:
    """Tests for the models.Sense model."""

    @pytest.fixture
    def entry(self, english_project):
        """A LexiconEntry to associate Senses with."""
        return models.LexiconEntry.objects.create(
            project=english_project, text="testword"
        )

    def test_create_valid_sense(self, entry):
        """Test creating a Sense with required fields."""
        sense = models.Sense.objects.create(entry=entry, eng="A test meaning")
        assert sense.pk is not None
        assert sense.entry == entry
        assert sense.eng == "a test meaning"  # lowercased on save
        assert sense.order == 1  # default
        assert sense.oth_lang is None
        assert sense.example is None

    def test_create_sense_with_all_fields(self, entry):
        """Test creating a Sense with all fields populated."""
        sense = models.Sense.objects.create(
            entry=entry,
            eng="Another Meaning",
            oth_lang="Tok Pisin Meaning",
            example="This is an example sentence.",
            order=2,
        )
        assert sense.eng == "another meaning"
        assert sense.oth_lang == "tok pisin meaning"
        assert sense.example == "This is an example sentence."
        assert sense.order == 2

    def test_entry_required(self):
        """Test that the 'entry' field is required."""
        with pytest.raises(ValidationError) as excinfo:
            sense = models.Sense(eng="A meaning without an entry")
            sense.full_clean()
        assert "entry" in excinfo.value.message_dict

    def test_eng_required(self, entry):
        """Test that the 'eng' field is required."""
        with pytest.raises(ValidationError) as excinfo:
            sense = models.Sense(entry=entry, eng="")  # blank is not allowed
            sense.full_clean()
        assert "eng" in excinfo.value.message_dict

    def test_lowercase_on_save(self, entry):
        """Test that 'eng' and 'oth_lang' are lowercased on save."""
        sense = models.Sense.objects.create(
            entry=entry, eng="UPPERCASE ENGLISH", oth_lang="UPPERCASE OTHER"
        )
        assert sense.eng == "uppercase english"
        assert sense.oth_lang == "uppercase other"

    def test_str_method(self, entry):
        """Test the __str__ method."""
        sense = models.Sense.objects.create(entry=entry, eng="A meaning", order=5)
        assert str(sense) == f"Sense 5 for {entry.text}"

    def test_cascade_delete(self, entry):
        """Test that deleting a LexiconEntry deletes its Senses."""
        sense = models.Sense.objects.create(entry=entry, eng="To be deleted")
        sense_pk = sense.pk
        assert models.Sense.objects.filter(pk=sense_pk).exists()
        entry.delete()
        assert not models.Sense.objects.filter(pk=sense_pk).exists()

    def test_ordering(self, entry):
        """Test that Senses are ordered by the 'order' field."""
        sense2 = models.Sense.objects.create(entry=entry, eng="Second", order=2)
        sense1 = models.Sense.objects.create(entry=entry, eng="First", order=1)
        sense3 = models.Sense.objects.create(entry=entry, eng="Third", order=3)

        senses_for_entry = models.Sense.objects.filter(entry=entry)
        assert list(senses_for_entry) == [sense1, sense2, sense3]

    def test_max_length_eng(self, entry):
        """Test max_length for eng field."""
        with pytest.raises(ValidationError) as excinfo:
            sense = models.Sense(entry=entry, eng="a" * 61)
            sense.full_clean()
        assert "eng" in excinfo.value.message_dict
        assert (
            "Ensure this value has at most 60 characters"
            in excinfo.value.message_dict["eng"][0]
        )

    def test_max_length_oth_lang(self, entry):
        """Test max_length for oth_lang field."""
        with pytest.raises(ValidationError) as excinfo:
            sense = models.Sense(entry=entry, eng="ok", oth_lang="a" * 61)
            sense.full_clean()
        assert "oth_lang" in excinfo.value.message_dict
        assert (
            "Ensure this value has at most 60 characters"
            in excinfo.value.message_dict["oth_lang"][0]
        )


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
        english_project.text_validator = r"[a-z]+"
        english_project.save()
        word = models.LexiconEntry.objects.create(text="word", project=english_project)
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
        word = models.LexiconEntry.objects.create(text="word", project=english_project)
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
        word = models.LexiconEntry.objects.create(project=english_project, text="word")
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
        word = models.LexiconEntry.objects.create(project=english_project, text="word")
        variation = models.Variation.objects.create(
            word=word, type="dialect", text="dialectvar"
        )
        s = str(variation)
        assert "Variation for: 'Word: word in English'" in s
        assert "dialectvar" in s
        assert "Dialectal Variant" in s

    def test_type_choices(self, english_project):
        word = models.LexiconEntry.objects.create(project=english_project, text="word")
        # Valid type
        models.Variation.objects.create(word=word, type="spelling", text="ok")
        # Invalid type
        with pytest.raises(ValidationError):
            v = models.Variation(word=word, type="notatype", text="fail")
            v.full_clean()

    def test_text_required_and_max_length(self, english_project):
        word = models.LexiconEntry.objects.create(project=english_project, text="word")
        # Required
        with pytest.raises(ValidationError):
            v = models.Variation(word=word, type="spelling", text=None)
            v.full_clean()
        # Max length
        with pytest.raises(ValidationError):
            v = models.Variation(word=word, type="spelling", text="a" * 101)
            v.full_clean()

    def test_get_absolute_url(self, english_project):
        word = models.LexiconEntry.objects.create(project=english_project, text="word")
        variation = models.Variation.objects.create(
            word=word, type="spelling", text="spellingvar"
        )
        url = variation.get_absolute_url()
        assert str(word.pk) in url
        assert word.project.language_code in url


@pytest.mark.django_db
class TestAffixModel:
    def test_create_valid_affix(self, english_project):
        affix = models.Affix.objects.create(
            project=english_project,
            name="Prefix A",
            applies_to="n",
            affix_letter="A",
        )
        assert affix.pk is not None
        assert affix.affix_letter == "A"
        assert affix.project == english_project

    def test_affix_letter_choices(self, english_project):
        # Valid uppercase
        models.Affix.objects.create(
            project=english_project, name="Prefix B", applies_to="n", affix_letter="B"
        )
        # Invalid lowercase
        affix = models.Affix(
            project=english_project, name="Prefix b", applies_to="n", affix_letter="b"
        )
        with pytest.raises(ValidationError):
            affix.full_clean()
        # Invalid non-letter
        affix = models.Affix(
            project=english_project, name="Prefix 1", applies_to="n", affix_letter="1"
        )
        with pytest.raises(ValidationError):
            affix.full_clean()

    def test_applies_to_choices(self, english_project):
        # Valid
        models.Affix.objects.create(
            project=english_project, name="Verb Affix", applies_to="v", affix_letter="C"
        )
        # Invalid
        affix = models.Affix(
            project=english_project,
            name="Invalid POS",
            applies_to="xyz",
            affix_letter="D",
        )
        with pytest.raises(ValidationError):
            affix.full_clean()

    def test_affix_letter_unique_per_project(self, english_project):
        models.Affix.objects.create(
            project=english_project, name="Affix1", applies_to="n", affix_letter="E"
        )
        with pytest.raises(IntegrityError):
            models.Affix.objects.create(
                project=english_project, name="Affix2", applies_to="v", affix_letter="E"
            )

    def test_affix_letter_can_repeat_across_projects(
        self, english_project, kovol_project
    ):
        models.Affix.objects.create(
            project=english_project, name="Affix1", applies_to="n", affix_letter="F"
        )
        # Should be allowed in a different project
        affix = models.Affix.objects.create(
            project=kovol_project, name="Affix2", applies_to="n", affix_letter="F"
        )
        assert affix.pk is not None

    def test_name_max_length(self, english_project):
        affix = models.Affix(
            project=english_project, name="a" * 41, applies_to="n", affix_letter="G"
        )
        with pytest.raises(ValidationError):
            affix.full_clean()

    def test_affix_letter_max_length(self, english_project):
        affix = models.Affix(
            project=english_project, name="Valid", applies_to="n", affix_letter="GH"
        )
        with pytest.raises(ValidationError):
            affix.full_clean()

    def test_str_method(self, english_project):
        affix = models.Affix.objects.create(
            project=english_project, name="Suffix", applies_to="n", affix_letter="H"
        )
        assert str(affix) == f"Affix H for {english_project.language_name}"
