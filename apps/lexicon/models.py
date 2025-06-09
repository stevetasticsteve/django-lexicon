import logging
import re

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

from apps.lexicon.tasks import update_lexicon_entry_search_field

log = logging.getLogger("lexicon")


def regex_validator_factory(project, field_name="value"):
    """Build a regex to use for entry validation for a given field."""

    def validator(value):
        pattern = project.tok_ples_validator
        if pattern:
            try:
                regex = re.compile(pattern, re.IGNORECASE)
            except re.error:
                raise ValidationError(f"Invalid regex pattern for {field_name}.")
            if not regex.fullmatch(value):
                log.debug(f"Validation for '{value}' failed due to regex.")
                raise ValidationError(
                    f"{field_name.capitalize()} '{value}' contains unallowed characters. A project admin set this restriction."
                )
            else:
                log.debug(f"Validation for '{value}' passed.")

    return validator


def normalize_and_validate(value, project, field_name="value"):
    """Apply a regex pattern to a value and apply lowercase enforcement."""
    log.debug(
        f"Running validation for '{value}'. project = '{project}', regex= '{project.tok_ples_validator}'"
    )
    value = value.lower()
    validator = regex_validator_factory(project, field_name)
    validator(value)
    return value


class LexiconProject(models.Model):
    """Represents a unique language to build a lexicon for."""

    # fields
    language_name = models.CharField(
        max_length=45, blank=False, null=False, verbose_name="Language name"
    )
    language_code = models.CharField(
        max_length=4,
        blank=False,
        null=False,
        unique=True,
        verbose_name="3 Digit ethnologue language code",
    )
    secondary_language = models.CharField(
        max_length=45,
        blank=True,
        null=True,
        help_text="An optional 2nd language, Tok Pisin for PNG langages",
    )
    version = models.IntegerField(
        verbose_name="version",
        blank=False,
        null=False,
        default=0,
    )
    tok_ples_validator = models.CharField(
        verbose_name="Regex Tok ples validator",
        help_text="An optional regex to represent which characters are allowed in Tok Ples entries. If set entries can only be saved if they only contain these characters. [abc] for example only allows the characters a, b and c.",
        blank=True,
        null=True,
        max_length=60,
    )
    affix_file = models.TextField(
        blank=False,
        null=False,
        help_text="See https://www.systutorials.com/docs/linux/man/4-hunspell/",
        default="""# Hunspell affix file for Kovol by NTMPNG
SET UTF-8
TRY aeiouAEIOUpbtdkgjmnfsvhlrwyPBTDKGJMNFSVHLRWY
WORDCHARS -

NOSUGGEST !""",
    )

    # methods
    def __str__(self):
        """What Python calls this object when it shows it on screen."""
        return f"{self.language_name} lexicon project"

    def clean(self):
        super().clean()
        if self.tok_ples_validator:
            try:
                re.compile(self.tok_ples_validator)
            except re.error:
                raise ValidationError(
                    {"tok_ples_validator": "This is not a valid regular expression."}
                )


class LexiconEntry(models.Model):
    "A representation of a word in a lexicon project."

    # fields
    project = models.ForeignKey(
        LexiconProject,
        on_delete=models.CASCADE,
        related_name="entries",
        blank=False,
        null=False,
    )
    tok_ples = models.CharField(
        verbose_name="Tok Ples",
        help_text="The language the project is focussed on.",
        max_length=60,
        null=False,
        blank=False,
    )
    search = models.TextField(
        blank=True, null=True, help_text="automatically generated search terms"
    )
    eng = models.CharField(
        verbose_name="English",
        max_length=60,
        null=True,
        blank=False,
    )
    oth_lang = models.CharField(
        verbose_name="Other language",
        max_length=60,
        null=True,
        blank=True,
        help_text="Translation in project 2nd language.",
    )
    comments = models.TextField(
        null=True,
        blank=True,
        help_text="extra comments or an extended definition information",
        max_length=1000,
    )
    review = models.CharField(
        choices=(
            ("0", "No review"),
            ("1", "Review now"),
            ("2", "Review after literacy"),
        ),
        max_length=1,
        help_text="Should this word be marked for review?",
        default="0",
        null=False,
    )
    review_comments = models.TextField(
        blank=True,
        null=True,
    )
    review_user = models.CharField(max_length=45, editable=False, blank=True, null=True)
    review_time = models.DateField(editable=False, null=True)
    created = models.DateField(editable=False, auto_now_add=True)
    modified = models.DateField(editable=False, auto_now=True)
    modified_by = models.CharField(editable=False, blank=True, null=True, max_length=45)

    pos = models.CharField(
        verbose_name="part of speech",
        max_length=5,
        blank=True,
        null=True,
        choices=(
            ("n", "noun"),
            ("pn", "proper noun"),
            ("adj", "adjective"),
            ("v", "verb"),
            ("adv", "adverb"),
            ("com", "compound verb"),
            ("prn", "pronoun"),
            ("rel", "relator/preposition"),
            ("uk", "uknown"),
        ),
    )

    checked = models.BooleanField(default=False, blank=False, null=False)
    paradigms = models.ManyToManyField(
        "Paradigm",
        blank=True,
        help_text="Paradigms that this word can use for conjugation/declension",
    )

    # Methods
    def __str__(self):
        """What Python calls this object when it shows it on screen."""
        return f"Word: {self.tok_ples} in {self.project.language_name}"

    def get_absolute_url(self):
        """What page Django should return if asked to show this entry."""
        # Return the detail page for the word
        return reverse(
            "lexicon:entry_detail", args=(self.project.language_code, self.pk)
        )

    def clean(self):
        """
        Custom validation for the LexiconEntry model.
        Checks tok_ples against the project's tok_ples_validator regex.
        """
        super().clean()  # Call the parent's clean method first
        if (
            self.project_id
        ):  # Use project_id for existence check during initial creation
            self.tok_ples = normalize_and_validate(
                self.tok_ples, self.project, "Tok ples"
            )

    def save(self, *args, **kwargs):
        """Code that runs whenever a Lexicon entry is saved.

        Lower case should be enforced and the version number updated if the tok_ples
        changes.
        The version number is used mostly to keep track of spell check exports,
        we don't want users downloading new spell checks when no spelling data
        has changed."""
        self.tok_ples = self.tok_ples.lower()
        if self.eng:
            self.eng = self.eng.lower()
        if self.oth_lang:
            self.oth_lang = self.oth_lang.lower()

        original_tok_ples = None
        # Fetch original tok_ples only if this is an existing object
        if self.pk:
            try:
                original_tok_ples = LexiconEntry.objects.get(pk=self.pk).tok_ples
            except LexiconEntry.DoesNotExist:
                # Should not happen if self.pk exists, but defensive
                pass

        self.project.save()  # Save the project to update its version
        # Perform the actual save first to ensure it's in the DB
        # and to catch any integrity errors before updating project version.
        super(LexiconEntry, self).save(*args, **kwargs)

        # Now check if tok_ples changed from its original (pre-save) value
        # and if it's not a new object (pk exists after save)
        if original_tok_ples and original_tok_ples != self.tok_ples:
            self.project.version += 1
            self.project.save()  # Save the project to update its version

        # trigger a celery task to update the search field
        update_lexicon_entry_search_field(self.pk)

    class Meta:
        ordering = ["tok_ples"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "tok_ples"], name="unique_tok_ples_per_project"
            )
        ]
        indexes = [models.Index(fields=["search"])]


class Variation(models.Model):
    """An allowed variation for a LexiconEntry."""

    word = models.ForeignKey(
        LexiconEntry, on_delete=models.CASCADE, related_name="variations"
    )
    type = models.CharField(
        max_length=15,
        choices=[
            ("spelling", "Spelling Variant"),
            ("dialect", "Dialectal Variant"),
            ("abbrv", "Abbreviation"),
        ],
    )
    text = models.CharField(
        verbose_name="variation",
        max_length=100,
        blank=False,
        null=False,
        help_text="write the variation here",
    )
    included_in_spellcheck = models.BooleanField(
        default=False, help_text="Should word be marked in spellcheck as acceptable?"
    )
    included_in_search = models.BooleanField(
        default=False, help_text="Should word appear in search results?"
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """What Python calls this object when it shows it on screen."""
        return (
            f"Variation for: '{self.word}' - '{self.text}' ({self.get_type_display()})"
        )
    
    def save(self,*args, **kwargs):
        # trigger a celery task to rebuild search index
        update_lexicon_entry_search_field(self.word.pk)
        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        """What page Django should return if asked to show this entry."""
        # Return the detail page for the main word
        return reverse(
            "lexicon:entry_detail", args=(self.word.project.language_code, self.word.pk)
        )


class IgnoreWord(models.Model):
    """A list of irregular words to be included in the spell check.

    Foreign words, names and transliterated words would all be good to include in
    the spellcheck. To avoid these crowding out Kovol words in the main dict
    view these are maintained as a seperate list. When building the .oxt spell
    check extension these can be included with a /NOSUGGEST tag.
    """

    tok_ples = models.CharField(
        max_length=60,
        blank=False,
        null=False,
        unique=True,
        help_text="Word to add to spell check.",
    )
    project = models.ForeignKey(
        LexiconProject,
        on_delete=models.CASCADE,
        related_name="ignore_word_project",
        blank=False,
        null=False,
    )
    type = models.CharField(
        max_length=3,
        blank=False,
        null=False,
        choices=(
            ("tpi", "Tok Pisin"),
            ("pn", "Proper noun"),
            ("eng", "English"),
            ("fgn", "Foreign transliterated"),
        ),
        help_text="Type of word to add to spell check.",
    )
    eng = models.CharField(
        max_length=60,
        blank=False,
        null=False,
        help_text="English",
        verbose_name="English",
    )
    comments = models.TextField(
        null=True,
        blank=True,
        help_text="extra comments or an extended definition information",
        max_length=300,
    )

    def save(self, *args, **kwargs):
        """Code that runs whenever a Lexicon entry is saved."""
        # enforce lower case
        self.tok_ples = self.tok_ples.lower()
        return super(IgnoreWord, self).save(*args, **kwargs)

    def __str__(self):
        """What Python calls this object when it shows it on screen."""
        return f"Ignore word: {self.tok_ples}"

    def get_absolute_url(self):
        """What page Django should return if asked to show this entry."""
        # return the ignore words list page
        return reverse("lexicon:ignore-update", args=(self.pk,))

    class Meta:
        ordering = ["tok_ples"]


class Paradigm(models.Model):
    """Represents a user defined word paradigm which can be used flexibly.

    A paradigm is used in templates to display entries in a grid."""

    name = models.CharField(max_length=40)
    project = models.ForeignKey(LexiconProject, on_delete=models.CASCADE)
    part_of_speech = models.CharField(
        max_length=5,
        blank=False,
        null=False,
        choices=LexiconEntry._meta.get_field("pos").choices,
        help_text="Part of speech this paradigm is for (e.g., verb, noun)",
    )
    row_labels = models.JSONField(
        help_text="List of row labels for the paradigm grid", blank=False, null=False
    )
    column_labels = models.JSONField(
        help_text="List of column labels for the paradigm grid", blank=False, null=False
    )

    def clean(self):
        if not isinstance(self.row_labels, list) or not isinstance(
            self.column_labels, list
        ):
            raise ValidationError("Row and column labels must be lists.")

    class Meta:
        # enforce unique paradigm names per project
        constraints = [
            models.UniqueConstraint(
                fields=["project", "name"], name="unique_paradigm_name_per_project"
            )
        ]

    def __str__(self):
        """What Python calls this object when it shows it on screen."""
        return f"{self.name} {self.part_of_speech} paradigm"


class Conjugation(models.Model):
    """
    A single cell in a conjugation paradigm grid.

    Each instance represents one form of a word based on a paradigm,
    identified by its row and column index in the grid.
    """

    word = models.ForeignKey(
        LexiconEntry,
        on_delete=models.CASCADE,
        help_text="The word that this conjugation belongs to.",
        blank=False,
        null=False,
    )
    paradigm = models.ForeignKey(
        Paradigm,
        on_delete=models.CASCADE,
        help_text="The paradigm that defines the conjugation structure.",
        blank=False,
        null=False,
    )
    row = models.IntegerField(
        null=False, blank=False, help_text="The row index in the paradigm grid."
    )
    column = models.IntegerField(
        null=False, blank=False, help_text="The column index in the paradigm grid."
    )
    conjugation = models.CharField(
        max_length=40,
        null=False,
        blank=True,
        help_text="The actual conjugated form of the word.",
    )

    def __str__(self):
        """What Python calls this object when it shows it on screen."""
        if self.conjugation:
            return (
                f"{self.conjugation}, a conjugation for {self.word} in {self.paradigm}"
            )
        else:
            return f"Empty conjugation for {self.word} in {self.paradigm}"

    def clean(self):
        """Run Tok ples validator over input."""
        super().clean()
        # Only validate if word is set (i.e., not a new/empty form)
        if self.word_id:
            project = self.word.project
            if project and project.tok_ples_validator:
                self.conjugation = normalize_and_validate(
                    self.conjugation, project, "conjugation"
                )

    def save(self, *args, **kwargs):
        """Only save lower case."""
        self.full_clean()
        if self.conjugation:
            self.conjugation = self.conjugation.lower()
        super().save(*args, **kwargs)

    def get_position_display(self):
        """Return a human-readable string representing the grid position."""
        return f"Row {self.row}, Column {self.column}"

    def get_grid_labels(self):
        """Return the row and column labels for this conjugation's position."""
        try:
            row_label = self.paradigm.row_labels[self.row]
            col_label = self.paradigm.column_labels[self.column]
            return f"{row_label}, {col_label}"
        except (IndexError, TypeError):
            return self.get_position_display()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["word", "paradigm", "row", "column"],
                name="unique_conjugation_position",
            )
        ]
        verbose_name = "Conjugation"
        verbose_name_plural = "Conjugations"
