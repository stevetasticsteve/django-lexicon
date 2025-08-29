import csv
import logging
import os

import django
from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.lexicon import models  # noqa: E402
from apps.lexicon.tasks import update_lexicon_entry_search_field  # noqa: E402


def parse_data():
    rows = []
    data = []
    with open("data/KuyuLexicon.csv", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            rows.append(row)
    for row in rows:
        d = {}
        d["orthography"] = row.get("Orthographic Spelling")
        d["verb_category"] = row.get("Verb Category")
        d["eng"] = row.get("Gloss")
        d["part_of_speech"] = row.get("Part of Speech")
        data.append(d)
    return data


def create_affixes(project):
    affixes = [
        {"letter": "A", "name": "ata", "applies_to": "v"},
        {"letter": "B", "name": "ta", "applies_to": "v"},
        {"letter": "C", "name": "ota", "applies_to": "v"},
        {"letter": "D", "name": "ma negation", "applies_to": "v"},
    ]
    for a in affixes:
        try:
            models.Affix.objects.create(
                affix_letter=a["letter"],
                name=a["name"],
                applies_to=a["applies_to"],
                project=project,
            )
        except django.db.utils.IntegrityError:
            pass


def create_lexicon_entry(data, project):
    log = logging.getLogger("lexicon")
    entry = models.LexiconEntry.objects.create(
        project=project,
        text=data.get("orthography"),
        pos=data.get("part_of_speech"),
        disambiguation=data.get("disambiguation", "")
    )
    try:
        models.Sense.objects.create(entry=entry, eng=data.get("eng"))
    except django.db.utils.DataError:
        # gloss is too long
        log.info(f"truncating gloss for {data.get('orthography')}")
        eng = data.get("eng")[0:59]
        models.Sense.objects.create(entry=entry, eng=eng)
        entry.comments = data.get("eng")
        entry.save()
    if data.get("verb_category"):
        afx = models.Affix.objects.filter(
            name__iexact=data.get("verb_category"), project=project
        ).first()
        if afx:
            entry.affixes.add(afx)
            entry.save()
    if data.get("part_of_speech") == "v":
        negation_pfx = models.Affix.objects.get(
            affix_letter="D", project=project)
        entry.affixes.add(negation_pfx)
        entry.save()
    update_lexicon_entry_search_field(entry.pk)
    return entry


def __main__():
    log = logging.getLogger("lexicon")
    log.setLevel(logging.ERROR)

    # create or get Kuyu project
    try:
        models.LexiconProject.objects.get(language_code="kqa").delete()
    except models.LexiconProject.DoesNotExist:
        pass
        
    kuyu_project = models.LexiconProject.objects.create(
            language_name="Kuyu",
            language_code="kqa",
            secondary_language="Tok Pisin",
        )

    data = parse_data()
    create_affixes(kuyu_project)
    for d in data:
        try:
            create_lexicon_entry(d, kuyu_project)
        except django.db.utils.IntegrityError:
            # add a digit to disambiguate
            count = models.LexiconEntry.objects.filter(
                project=kuyu_project, text=d.get("orthography")
            ).count()
            d["disambiguation"] = str(count + 1)
            log.info(f"adding disambiguation {d.get('disambiguation')}")
            create_lexicon_entry(d, kuyu_project)

        except Exception as e:
            log.error(f"Error creating entry for data {d}: {e}")


if __name__ == "__main__":
    __main__()
    print("Data import completed successfully.")
