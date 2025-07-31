import json
import os

import django
from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.lexicon import models # noqa: E402


def import_kovol_data(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        old_data = json.load(file)
    return old_data


def __main__():
    file_path = "data/CLAHub.json"
    old_data = import_kovol_data(file_path)

    kovol_word_model = []
    lexicon_entry_model = []
    lexicon_word_affix = []
    lexicon_kovolwordsense = []
    lexicon_kovolwordspellingvariation = []

    for item in old_data:
        match item["model"]:
            case "lexicon.kovolword":
                kovol_word_model.append(item)
            case "lexicon.lexiconentry":
                lexicon_entry_model.append(item)
            case "lexicon.wordaffix":
                lexicon_word_affix.append(item)
            case "lexicon.kovolwordsense":
                lexicon_kovolwordsense.append(item)
            case "lexicon.kovolwordspellingvariation":
                lexicon_kovolwordspellingvariation.append(item)

    # create or get Kovol project
    try:
        kovol_project = models.LexiconProject.objects.get(language_code="kgu")
    except models.LexiconProject.DoesNotExist:
        kovol_project = models.LexiconProject.objects.create(
            language_name="Kovol",
            language_code="kgu",
            secondary_language="Tok Pisin",
        )

    # create the Kovol Word Objects
    for kw in kovol_word_model:
        pk = kw["pk"]
        lexicon_entry = next(
            (record for record in lexicon_entry_model if record.get("pk") == pk),
            None,
        )
        word = models.LexiconEntry.objects.create(
            pk=pk,
            project=kovol_project,
            text=kw["fields"]["kgu"],
            checked=kw["fields"]["checked"],
            pos=kw["fields"]["pos"],
            comments=lexicon_entry["fields"]["comments"],
            review=lexicon_entry["fields"]["review"],
            review_comments=lexicon_entry["fields"]["review_comments"],
            review_user=lexicon_entry["fields"]["review_user"],
            review_time=lexicon_entry["fields"]["review_time"],
            created=lexicon_entry["fields"]["created"],
            modified=lexicon_entry["fields"]["modified"],
            modified_by=lexicon_entry["fields"]["modified_by"],
        )

        # get the additional senses
        models.Sense.objects.create(entry=word, eng=lexicon_entry["fields"]["eng"], oth_lang=lexicon_entry["fields"]["tpi"])
        senses = [s for s in lexicon_kovolwordsense if s["fields"]["word"] == pk]
        if senses:
            for sense in senses:
                models.Sense.objects.create(
                    entry=word,
                    eng=sense["fields"]["sense"])
        
        # get the matat spelling
        if kw["fields"]["matat"] and kw["fields"]["matat"] != kw["fields"]["kgu"]:
            models.Variation.objects.create(word=word, type="dialect", text=kw["fields"]["matat"])
        
        # get the spelling variations
        spelling_variations = [
            sv for sv in lexicon_kovolwordspellingvariation if sv["fields"]["word"] == pk
        ]
        for sv in spelling_variations:
            models.Variation.objects.create(
                word=word,
                type="spelling",
                text=sv["fields"]["spelling_variation"],
            )

        # lexicon_kovolword_affixes
        # verbs
        # phrases


if __name__ == "__main__":
    __main__()
    print("Data import completed successfully.")
