import json

import pytest

from apps.lexicon.models import (
    Affix,
    Conjugation,
    IgnoreWord,
    LexiconEntry,
    LexiconProject,
    Paradigm,
    Sense,
    Variation,
)
from apps.lexicon.utils.project_import_export import (
    export_project,
    export_project_to_json,
    import_project,
    import_project_from_json,
)

# --- Fixtures ---


@pytest.fixture
def project(db):
    return LexiconProject.objects.create(
        language_name="Kovol",
        language_code="kgu",
        secondary_language="Tok Pisin",
        text_validator="[a-z ]+",
        affix_file="# test affix file",
    )


@pytest.fixture
def paradigm(project):
    return Paradigm.objects.create(
        project=project,
        name="verb conjugation",
        part_of_speech="v",
        row_labels=["1sg", "2sg", "3sg"],
        column_labels=["present", "past"],
    )


@pytest.fixture
def affix(project):
    return Affix.objects.create(
        project=project,
        name="plural suffix",
        applies_to="n",
        affix_letter="A",
    )


@pytest.fixture
def entry(project, paradigm, affix):
    e = LexiconEntry.objects.create(
        project=project,
        text="amun",
        disambiguation="",
        comments="a test word",
        review="0",
        pos="v",
        checked=True,
    )
    e.paradigms.add(paradigm)
    e.affixes.add(affix)
    Sense.objects.create(entry=e, eng="to walk", oth_lang="wokabaut", order=1)
    Sense.objects.create(entry=e, eng="to travel", oth_lang=None, order=2)
    Variation.objects.create(
        word=e,
        type="dialect",
        text="amung",
        included_in_spellcheck=True,
        included_in_search=False,
    )
    Conjugation.objects.create(
        word=e, paradigm=paradigm, row=0, column=0, conjugation="amamun"
    )
    return e


@pytest.fixture
def ignore_word(project):
    return IgnoreWord.objects.create(
        project=project, text="jesus", type="pn", eng="Jesus"
    )


@pytest.fixture
def full_project(project, paradigm, affix, entry, ignore_word):
    """A project with all related objects populated."""
    return project


# --- Export tests ---


class TestExport:
    def test_export_returns_dict(self, full_project):
        data = export_project(full_project.pk)
        assert isinstance(data, dict)

    def test_export_version_present(self, full_project):
        data = export_project(full_project.pk)
        assert data["export_version"] == 1

    def test_project_fields_exported(self, full_project):
        data = export_project(full_project.pk)
        p = data["project"]
        assert p["language_code"] == "kgu"
        assert p["language_name"] == "Kovol"
        assert p["secondary_language"] == "Tok Pisin"

    def test_paradigms_exported(self, full_project):
        data = export_project(full_project.pk)
        assert len(data["paradigms"]) == 1
        assert data["paradigms"][0]["name"] == "verb conjugation"
        assert data["paradigms"][0]["row_labels"] == ["1sg", "2sg", "3sg"]

    def test_affixes_exported(self, full_project):
        data = export_project(full_project.pk)
        assert len(data["affixes"]) == 1
        assert data["affixes"][0]["affix_letter"] == "A"

    def test_entries_exported(self, full_project):
        data = export_project(full_project.pk)
        assert len(data["entries"]) == 1
        entry = data["entries"][0]
        assert entry["text"] == "amun"
        assert entry["checked"] is True

    def test_entry_senses_exported(self, full_project):
        data = export_project(full_project.pk)
        senses = data["entries"][0]["senses"]
        assert len(senses) == 2
        assert senses[0]["eng"] == "to walk"
        assert senses[0]["oth_lang"] == "wokabaut"

    def test_entry_variations_exported(self, full_project):
        data = export_project(full_project.pk)
        variations = data["entries"][0]["variations"]
        assert len(variations) == 1
        assert variations[0]["text"] == "amung"
        assert variations[0]["included_in_spellcheck"] is True

    def test_entry_conjugations_exported(self, full_project):
        data = export_project(full_project.pk)
        conjugations = data["entries"][0]["conjugations"]
        assert len(conjugations) == 1
        assert conjugations[0]["conjugation"] == "amamun"
        assert conjugations[0]["row"] == 0

    def test_entry_m2m_paradigms_exported(self, full_project, paradigm):
        data = export_project(full_project.pk)
        assert paradigm.pk in data["entries"][0]["paradigm_local_ids"]

    def test_ignore_words_exported(self, full_project):
        data = export_project(full_project.pk)
        assert len(data["ignore_words"]) == 1
        assert data["ignore_words"][0]["text"] == "jesus"

    def test_export_to_json_is_valid_json(self, full_project):
        json_str = export_project_to_json(full_project.pk)
        parsed = json.loads(json_str)
        assert parsed["project"]["language_code"] == "kgu"

    def test_empty_project_exports_cleanly(self, project):
        data = export_project(project.pk)
        assert data["entries"] == []
        assert data["paradigms"] == []
        assert data["affixes"] == []
        assert data["ignore_words"] == []


# --- Import tests ---


class TestImport:
    def test_basic_import_creates_project(self, db, full_project):
        data = export_project(full_project.pk)
        full_project.delete()

        imported = import_project(data)
        assert LexiconProject.objects.filter(language_code="kgu").exists()
        assert imported.language_name == "Kovol"

    def test_import_creates_paradigms(self, db, full_project):
        data = export_project(full_project.pk)
        full_project.delete()

        import_project(data)
        project = LexiconProject.objects.get(language_code="kgu")
        assert Paradigm.objects.filter(
            project=project, name="verb conjugation"
        ).exists()

    def test_import_creates_affixes(self, db, full_project):
        data = export_project(full_project.pk)
        full_project.delete()

        import_project(data)
        project = LexiconProject.objects.get(language_code="kgu")
        assert Affix.objects.filter(project=project, affix_letter="A").exists()

    def test_import_creates_entries(self, db, full_project):
        data = export_project(full_project.pk)
        full_project.delete()

        import_project(data)
        project = LexiconProject.objects.get(language_code="kgu")
        assert LexiconEntry.objects.filter(project=project, text="amun").exists()

    def test_import_creates_senses(self, db, full_project):
        data = export_project(full_project.pk)
        full_project.delete()

        import_project(data)
        entry = LexiconEntry.objects.get(text="amun")
        assert entry.senses.count() == 2
        assert entry.senses.filter(eng="to walk").exists()

    def test_import_creates_variations(self, db, full_project):
        data = export_project(full_project.pk)
        full_project.delete()

        import_project(data)
        entry = LexiconEntry.objects.get(text="amun")
        assert entry.variations.filter(text="amung").exists()

    def test_import_creates_conjugations(self, db, full_project):
        data = export_project(full_project.pk)
        full_project.delete()

        import_project(data)
        entry = LexiconEntry.objects.get(text="amun")
        assert entry.conjugations.filter(conjugation="amamun", row=0, column=0).exists()

    def test_import_restores_m2m_paradigms(self, db, full_project):
        data = export_project(full_project.pk)
        full_project.delete()

        import_project(data)
        entry = LexiconEntry.objects.get(text="amun")
        assert entry.paradigms.filter(name="verb conjugation").exists()

    def test_import_restores_m2m_affixes(self, db, full_project):
        data = export_project(full_project.pk)
        full_project.delete()

        import_project(data)
        entry = LexiconEntry.objects.get(text="amun")
        assert entry.affixes.filter(affix_letter="A").exists()

    def test_import_creates_ignore_words(self, db, full_project):
        data = export_project(full_project.pk)
        full_project.delete()

        import_project(data)
        project = LexiconProject.objects.get(language_code="kgu")
        assert IgnoreWord.objects.filter(project=project, text="jesus").exists()

    def test_import_conflict_raises_without_overwrite(self, db, full_project):
        data = export_project(full_project.pk)
        with pytest.raises(ValueError, match="already exists"):
            import_project(data)

    def test_import_overwrite_replaces_project(self, db, full_project):
        data = export_project(full_project.pk)
        import_project(data, overwrite=True)
        assert LexiconProject.objects.filter(language_code="kgu").count() == 1

    def test_import_wrong_version_raises(self, db):
        data = {"export_version": 99, "project": {}}
        with pytest.raises(ValueError, match="Unsupported export version"):
            import_project(data)

    def test_roundtrip_via_json(self, db, full_project):
        json_str = export_project_to_json(full_project.pk)
        full_project.delete()

        import_project_from_json(json_str)
        assert LexiconProject.objects.filter(language_code="kgu").exists()
        assert LexiconEntry.objects.filter(text="amun").exists()
        assert Sense.objects.filter(eng="to walk").exists()
