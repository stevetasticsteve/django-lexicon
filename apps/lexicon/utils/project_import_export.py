# This module is for admins to import and export projects via a django management command

import json
import logging
from datetime import datetime, timezone

from django.db import transaction

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

log = logging.getLogger("lexicon")


def export_project(project_pk: int) -> dict:
    """
    Serialize a full LexiconProject and all related data to a dict.
    PKs are preserved in the export so relationships can be reconstructed,
    but they are treated as local IDs only — the importer remaps them.
    """
    project = LexiconProject.objects.get(pk=project_pk)

    entries = LexiconEntry.objects.filter(project=project).prefetch_related(
        "senses", "variations", "conjugations", "paradigms", "affixes"
    )
    paradigms = Paradigm.objects.filter(project=project)
    affixes = Affix.objects.filter(project=project)
    ignore_words = IgnoreWord.objects.filter(project=project)

    def serialize_project(p):
        return {
            "language_name": p.language_name,
            "language_code": p.language_code,
            "secondary_language": p.secondary_language,
            "version": p.version,
            "text_validator": p.text_validator,
            "affix_file": p.affix_file,
        }

    def serialize_paradigm(p):
        return {
            "local_id": p.pk,
            "name": p.name,
            "part_of_speech": p.part_of_speech,
            "row_labels": p.row_labels,
            "column_labels": p.column_labels,
        }

    def serialize_affix(a):
        return {
            "local_id": a.pk,
            "name": a.name,
            "applies_to": a.applies_to,
            "affix_letter": a.affix_letter,
        }

    def serialize_entry(e):
        return {
            "local_id": e.pk,
            "text": e.text,
            "disambiguation": e.disambiguation,
            "comments": e.comments,
            "review": e.review,
            "review_comments": e.review_comments,
            "pos": e.pos,
            "checked": e.checked,
            "paradigm_local_ids": list(e.paradigms.values_list("pk", flat=True)),
            "affix_local_ids": list(e.affixes.values_list("pk", flat=True)),
            "senses": [
                {
                    "eng": s.eng,
                    "oth_lang": s.oth_lang,
                    "example": s.example,
                    "order": s.order,
                }
                for s in e.senses.all()
            ],
            "variations": [
                {
                    "type": v.type,
                    "text": v.text,
                    "included_in_spellcheck": v.included_in_spellcheck,
                    "included_in_search": v.included_in_search,
                    "notes": v.notes,
                }
                for v in e.variations.all()
            ],
            "conjugations": [
                {
                    "paradigm_local_id": c.paradigm_id,
                    "row": c.row,
                    "column": c.column,
                    "conjugation": c.conjugation,
                }
                for c in e.conjugations.all()
            ],
        }

    def serialize_ignore_word(iw):
        return {
            "text": iw.text,
            "type": iw.type,
            "eng": iw.eng,
            "comments": iw.comments,
        }

    return {
        "export_version": 1,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "project": serialize_project(project),
        "paradigms": [serialize_paradigm(p) for p in paradigms],
        "affixes": [serialize_affix(a) for a in affixes],
        "entries": [serialize_entry(e) for e in entries],
        "ignore_words": [serialize_ignore_word(iw) for iw in ignore_words],
    }


def export_project_to_json(project_pk: int) -> str:
    return json.dumps(export_project(project_pk), indent=2, ensure_ascii=False)


@transaction.atomic
def import_project(data: dict, overwrite: bool = False) -> LexiconProject:
    """
    Import a project bundle produced by export_project().

    If overwrite=True and a project with the same language_code exists,
    it will be deleted and recreated. Otherwise a conflict raises ValueError.

    Returns the newly created LexiconProject.
    """
    if data.get("export_version") != 1:
        raise ValueError(f"Unsupported export version: {data.get('export_version')}")

    proj_data = data["project"]
    language_code = proj_data["language_code"]

    existing = LexiconProject.objects.filter(language_code=language_code).first()
    if existing:
        if overwrite:
            log.warning(f"Deleting existing project '{language_code}' for overwrite.")
            existing.delete()
        else:
            raise ValueError(
                f"A project with language_code '{language_code}' already exists. "
                "Pass overwrite=True to replace it."
            )

    project = LexiconProject.objects.create(
        language_name=proj_data["language_name"],
        language_code=language_code,
        secondary_language=proj_data.get("secondary_language"),
        version=proj_data["version"],
        text_validator=proj_data.get("text_validator"),
        affix_file=proj_data["affix_file"],
    )

    # --- Paradigms: build local_id -> new pk map ---
    paradigm_map: dict[int, Paradigm] = {}
    for p in data.get("paradigms", []):
        new_paradigm = Paradigm.objects.create(
            project=project,
            name=p["name"],
            part_of_speech=p["part_of_speech"],
            row_labels=p["row_labels"],
            column_labels=p["column_labels"],
        )
        paradigm_map[p["local_id"]] = new_paradigm

    # --- Affixes: build local_id -> new pk map ---
    affix_map: dict[int, Affix] = {}
    for a in data.get("affixes", []):
        new_affix = Affix.objects.create(
            project=project,
            name=a["name"],
            applies_to=a["applies_to"],
            affix_letter=a["affix_letter"],
        )
        affix_map[a["local_id"]] = new_affix

    # --- Entries ---
    for e in data.get("entries", []):
        # Use update_fields or direct field assignment to skip the version-bumping
        # save() override — we're restoring, not editing.
        entry = LexiconEntry(
            project=project,
            text=e["text"],
            disambiguation=e.get("disambiguation", ""),
            comments=e.get("comments"),
            review=e.get("review", "0"),
            review_comments=e.get("review_comments"),
            pos=e.get("pos"),
            checked=e.get("checked", False),
        )
        # Bypass the custom save() to avoid version bumps and Celery tasks
        # during a bulk restore. Call super().save() via the base class directly.
        LexiconEntry.save.__wrapped__(entry) if hasattr(
            LexiconEntry.save, "__wrapped__"
        ) else super(LexiconEntry, entry).save()

        # M2M relationships
        if e.get("paradigm_local_ids"):
            entry.paradigms.set(
                paradigm_map[lid]
                for lid in e["paradigm_local_ids"]
                if lid in paradigm_map
            )
        if e.get("affix_local_ids"):
            entry.affixes.set(
                affix_map[lid] for lid in e["affix_local_ids"] if lid in affix_map
            )

        # Senses
        Sense.objects.bulk_create(
            [
                Sense(
                    entry=entry,
                    eng=s["eng"],
                    oth_lang=s.get("oth_lang"),
                    example=s.get("example"),
                    order=s.get("order", 1),
                )
                for s in e.get("senses", [])
            ]
        )

        # Variations
        Variation.objects.bulk_create(
            [
                Variation(
                    word=entry,
                    type=v["type"],
                    text=v["text"],
                    included_in_spellcheck=v.get("included_in_spellcheck", False),
                    included_in_search=v.get("included_in_search", False),
                    notes=v.get("notes"),
                )
                for v in e.get("variations", [])
            ]
        )

        # Conjugations (paradigm_map lookup needed)
        Conjugation.objects.bulk_create(
            [
                Conjugation(
                    word=entry,
                    paradigm=paradigm_map[c["paradigm_local_id"]],
                    row=c["row"],
                    column=c["column"],
                    conjugation=c.get("conjugation", ""),
                )
                for c in e.get("conjugations", [])
                if c["paradigm_local_id"] in paradigm_map
            ]
        )

    # --- Ignore words ---
    IgnoreWord.objects.bulk_create(
        [
            IgnoreWord(
                project=project,
                text=iw["text"],
                type=iw["type"],
                eng=iw["eng"],
                comments=iw.get("comments"),
            )
            for iw in data.get("ignore_words", [])
        ]
    )

    log.info(f"Import complete for project '{language_code}'.")
    return project


def import_project_from_json(json_str: str, overwrite: bool = False) -> LexiconProject:
    data = json.loads(json_str)
    return import_project(data, overwrite=overwrite)
