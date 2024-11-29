from django.db import models
from django.core.validators import RegexValidator
from django.urls import reverse


import re
from decimal import Decimal


class LexiconProject(models.Model):
    """Represents a unique language to build a lexicon for."""

    language_name = models.CharField(
        max_length=25, blank=False, null=False, verbose_name="Language name"
    )
    language_code = models.CharField(
        max_length=4,
        blank=False,
        null=False,
        unique=True,
        verbose_name="3 Digit ethnologue language code",
    )
    secondary_language = models.CharField(
        max_length=25,
        blank=True,
        null=True,
        help_text="An optional 2nd language, Tok Pisin for PNG langages",
    )
    version = models.DecimalField(
        verbose_name="version",
        blank=False,
        null=False,
        decimal_places=3,
        max_digits=5,
        default=0.0,
    )
    tok_ples_validator = models.CharField(
        verbose_name="Regex Tok ples validator",
        help_text="An optional regex to represent which characters are allowed in Tok Ples entries. If set entries can only be saved if they only contain these characters. [abc] for example only allows the characters a, b and c.",
        blank=True,
        null=True,
        max_length=25,
    )

    def __str__(self):
        """What Python calls this object when it shows it on screen."""
        return f"{self.language_name} lexicon project"


# Lexicon entry models
class LexiconEntry(models.Model):
    "A base class other models can inherit from."

    project = models.ForeignKey(
        LexiconProject,
        on_delete=models.CASCADE,
        related_name="project",
        blank=False,
        null=False,
    )
    tok_ples = models.CharField(
        verbose_name="Tok Ples",
        help_text="The language the project is focussed on.",
        max_length=45,
        null=False,
        blank=False,
        unique=True,
        # validators=RegexValidator(
        #     regex=project.project.tok_ples_validator,
        #     message="You must only use allowed characters.",
        #     flags=re.IGNORECASE,
        # ),
    )
    eng = models.CharField(
        verbose_name="English",
        max_length=45,
        null=True,
        blank=False,
    )
    oth_lang = models.CharField(
        verbose_name="Other language",
        max_length=45,
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
    review_user = models.CharField(max_length=10, editable=False, blank=True, null=True)
    review_time = models.DateField(editable=False, null=True)
    created = models.DateField(editable=False, auto_now_add=True)
    modified = models.DateField(editable=False, auto_now=True)
    modified_by = models.CharField(editable=False, blank=True, null=True, max_length=10)

    pos = models.CharField(
        verbose_name="part of speech",
        max_length=5,
        blank=True,
        null=True,
        choices=(
            ("n", "noun"),
            ("pn", "proper noun"),
            ("adj", "adjective"),
            ("adv", "adverb"),
            ("com", "compound verb"),
            ("prn", "pronoun"),
            ("rel", "relator/preposition"),
            ("uk", "uknown"),
        ),
    )

    checked = models.BooleanField(default=False, blank=False, null=False)

    def save(self, *args, **kwargs):
        """Code that runs whenever a Lexicon entry is saved."""
        # Make all entries lower case
        self.tok_ples = self.tok_ples.lower()
        if self.eng:  # imports may be lacking, avoid a None type error
            self.eng = self.eng.lower()
        if self.oth_lang:  # this field is optional, avoid a None type error
            self.oth_lang = self.oth_lang.lower()
        # Increment the project's version number
        self.project.version += Decimal("0.001")
        self.project.save()

        return super(LexiconEntry, self).save(*args, **kwargs)

    def __str__(self):
        """What Python calls this object when it shows it on screen."""
        return f"Lexicon entry: {self.tok_ples}"

    def get_absolute_url(self):
        """What page Django should return if asked to show this entry."""
        # Return the detail page for the word
        return reverse(
            "lexicon:entry_detail", args=(self.project.language_code, self.pk)
        )


class SpellingVariation(models.Model):
    """An allowed spelling variation for a LexiconEntry."""

    word = models.ForeignKey(
        LexiconEntry, on_delete=models.CASCADE, related_name="spelling_variation"
    )
    spelling_variation = models.CharField(
        verbose_name="spelling variation",
        max_length=45,
        blank=False,
        null=False,
        help_text="write the spelling variation here",
        # validators=RegexValidator(
        #     regex=word.project.tok_ples_validator,
        #     message="You must only use allowed characters.",
        #     flags=re.IGNORECASE,
        # ),
    )

    def __str__(self):
        """What Python calls this object when it shows it on screen."""
        return f"Spelling variation for: {self.word.tok_ples}"

    def get_absolute_url(self):
        """What page Django should return if asked to show this entry."""
        # Return the detail page for the main word
        return reverse(
            "lexicon:entry_detail", args=(self.project.language_code, self.pk)
        )


class IgnoreWord(models.Model):
    """A list of irregular words to be included in the spell check.

    Foreign words, names and transliterated words would all be good to include in
    the spellcheck. To avoid these crowding out Kovol words in the main dict
    view these are maintained as a seperate list. When building the .oxt spell
    check extension these can be included with a /NOSUGGEST tag.
    """

    word = models.CharField(
        max_length=25,
        blank=False,
        null=False,
        unique=True,
        help_text="Word to add to spell check.",
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
        max_length=25,
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
        self.word = self.word.lower()
        return super(IgnoreWord, self).save(*args, **kwargs)

    def __str__(self):
        """What Python calls this object when it shows it on screen."""
        return f"Ignore word: {self.word}"

    def get_absolute_url(self):
        """What page Django should return if asked to show this entry."""
        # return the ignore words list page
        return reverse("lexicon:ignore-update", args=(self.pk,))

    class Meta:
        ordering = ["word"]
