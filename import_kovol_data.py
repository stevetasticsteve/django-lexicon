import json
import logging
import os

import django
from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.lexicon import models  # noqa: E402
from apps.lexicon.tasks import update_lexicon_entry_search_field  # noqa: E402


def import_kovol_data(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        old_data = json.load(file)
    return old_data


def parse_data():
    file_path = "data/CLAHub.json"
    old_data = import_kovol_data(file_path)

    # Initialize an empty dictionary to store data by model name
    parsed_data_by_model = {}

    for item in old_data:
        model_name = item.get("model")
        if model_name:
            # If the model name is not yet a key in the dictionary, add it with an empty list
            if model_name not in parsed_data_by_model:
                parsed_data_by_model[model_name] = []
            # Append the current item to the list associated with its model name
            parsed_data_by_model[model_name].append(item)

    return parsed_data_by_model


def import_word_data(kovol_project, data):
    # create the Kovol Word Objects
    for kw in data["lexicon.kovolword"]:
        pk = kw["pk"]
        lexicon_entry = next(
            (
                record
                for record in data["lexicon.lexiconentry"]
                if record.get("pk") == pk
            ),
            None,
        )
        word = models.LexiconEntry.objects.create(
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

        models.Sense.objects.create(
            entry=word,
            eng=lexicon_entry["fields"]["eng"],
            oth_lang=lexicon_entry["fields"]["tpi"],
        )
        # get the additional senses
        senses = [
            s for s in data["lexicon.kovolwordsense"] if s["fields"]["word"] == pk
        ]
        if senses:
            for sense in senses:
                models.Sense.objects.create(entry=word, eng=sense["fields"]["sense"])

        # get the matat spelling
        if kw["fields"]["matat"] and kw["fields"]["matat"] != kw["fields"]["kgu"]:
            models.Variation.objects.create(
                word=word, type="dialect", text=kw["fields"]["matat"]
            )

        # get the spelling variations
        spelling_variations = [
            sv
            for sv in data["lexicon.kovolwordspellingvariation"]
            if sv["fields"]["word"] == pk
        ]
        for sv in spelling_variations:
            models.Variation.objects.create(
                word=word,
                type="spelling",
                text=sv["fields"]["spelling_variation"],
                included_in_spellcheck=True,
                included_in_search=True,
            )
        # TOD the og affix


def get_affixes(kovol_project):
    affixes = {}
    affix_map = {
        "A": "-yam continuous aspect",
        "B": "-i durative aspect",
        "C": "-a simultaenous aspect",
        "D": "hi- instrument manner",
        "E": "ana- instrument manner",
        "F": "object prefix",
        "G": "wom- instrument manner",
    }
    for affix_letter, affix_name in affix_map.items():
        try:
            affix = models.Affix.objects.get(name=affix_name, project=kovol_project)
        except models.Affix.DoesNotExist:
            affix = models.Affix.objects.create(
                name=affix_name,
                project=kovol_project,
                applies_to="v",
                affix_letter=affix_letter,
            )
        affixes[affix_letter] = affix
    return affixes


def import_verb_data(kovol_project, data, log):
    # Get the related models
    verb_paradigm, enclitic_paradigm, imperatives_paradigm = get_paradigm_objects(
        kovol_project
    )
    affixes = get_affixes(kovol_project)

    # loop through the verbs and create the verb entries
    for kv in data["lexicon.lexiconverbentry"]:
        try:
            checked_counter = 0
            pk = kv["pk"]
            lexicon_entry = next(
                (
                    record
                    for record in data["lexicon.lexiconentry"]
                    if record.get("pk") == pk
                ),
                None,
            )
            # create the main entry
            verb = models.LexiconEntry.objects.create(
                project=kovol_project,
                text=kv["fields"]["future_1s"],
                checked=False,
                pos="v",
                comments=lexicon_entry["fields"]["comments"],
                review=lexicon_entry["fields"]["review"],
                review_comments=lexicon_entry["fields"]["review_comments"],
                review_user=lexicon_entry["fields"]["review_user"],
                review_time=lexicon_entry["fields"]["review_time"],
                created=lexicon_entry["fields"]["created"],
                modified=lexicon_entry["fields"]["modified"],
                modified_by=lexicon_entry["fields"]["modified_by"],
            )

            # Catch the IntegrityError for the 1s future tense
        except django.db.utils.IntegrityError:
            verb = models.LexiconEntry.objects.create(
                project=kovol_project,
                text=kv["fields"]["future_1s"],
                checked=False,
                pos="v",
                disambiguation="DISAMBIGUATION NEEDED",
                comments=lexicon_entry["fields"]["comments"],
                review=lexicon_entry["fields"]["review"],
                review_comments=lexicon_entry["fields"]["review_comments"],
                review_user=lexicon_entry["fields"]["review_user"],
                review_time=lexicon_entry["fields"]["review_time"],
                created=lexicon_entry["fields"]["created"],
                modified=lexicon_entry["fields"]["modified"],
                modified_by=lexicon_entry["fields"]["modified_by"],
            )
            log.info(f"{verb} created with disambiguation needed. pk={verb.pk}")

        # add the verb paradigms
        verb.paradigms.add(verb_paradigm)

        # Add all the conjugations
        conjugation_map = {
            "past_1s": (0, 0),
            "past_2s": (1, 0),
            "past_3s": (2, 0),
            "past_1p": (3, 0),
            "past_2p": (4, 0),
            "past_3p": (5, 0),
            "present_1s": (0, 1),
            "present_2s": (1, 1),
            "present_3s": (2, 1),
            "present_1p": (3, 1),
            "present_2p": (4, 1),
            "present_3p": (5, 1),
            "future_1s": (0, 2),
            "future_2s": (1, 2),
            "future_3s": (2, 2),
            "future_1p": (3, 2),
            "future_2p": (4, 2),
            "future_3p": (5, 2),
        }
        for c in conjugation_map:
            if kv["fields"][c]:
                models.Conjugation.objects.create(
                    word=verb,
                    paradigm=verb_paradigm,
                    row=conjugation_map[c][0],
                    column=conjugation_map[c][1],
                    conjugation=kv["fields"][c],
                )
            if kv["fields"][f"{c}_checked"]:
                checked_counter += 1
        # add the enclitics
        verb.paradigms.add(enclitic_paradigm)
        enclitic_map = {
            "enclitic_same_actor": (4, 0),
            "enclitic_1s": (0, 0),
            "enclitic_1p": (1, 0),
            "enclitic_2s": (2, 0),
            "enclitic_2p": (3, 0),
        }
        for c in enclitic_map:
            if kv["fields"][c]:
                models.Conjugation.objects.create(
                    word=verb,
                    paradigm=enclitic_paradigm,
                    row=enclitic_map[c][0],
                    column=enclitic_map[c][1],
                    conjugation=kv["fields"][c],
                )
            if kv["fields"][f"{c}_checked"]:
                checked_counter += 1
        # add the imperatives
        verb.paradigms.add(imperatives_paradigm)
        imperative_map = {
            "sg_imp": (0, 0),
            "pl_imp": (1, 0),
            "nominalizer": (0, 1),
            "iguwot": (0, 2),
        }
        for c in imperative_map:
            if kv["fields"][c]:
                models.Conjugation.objects.create(
                    word=verb,
                    paradigm=imperatives_paradigm,
                    row=imperative_map[c][0],
                    column=imperative_map[c][1],
                    conjugation=kv["fields"][c],
                )
            if kv["fields"][f"{c}_checked"]:
                checked_counter += 1
        # set the checked status
        if checked_counter >= 9:
            verb.checked = True
            verb.save()
        # Add the main sense
        models.Sense.objects.create(
            entry=verb,
            eng=lexicon_entry["fields"]["eng"],
            oth_lang=lexicon_entry["fields"]["tpi"],
        )
        # get the additional senses
        senses = [s for s in data["lexicon.verbsense"] if s["fields"]["verb"] == pk]
        if senses:
            for sense in senses:
                models.Sense.objects.create(entry=verb, eng=sense["fields"]["sense"])

        # get the spelling variations
        spelling_variations = [
            sv
            for sv in data["lexicon.verbspellingvariation"]
            if sv["fields"]["verb"] == pk
        ]
        # TODO losing the variation conjugation information here.
        for sv in spelling_variations:
            models.Variation.objects.create(
                word=verb,
                type="spelling",
                text=sv["fields"]["spelling_variation"],
                included_in_spellcheck=True,
                included_in_search=True,
            )

        # add the verb affixes
        verb.affixes.add(affixes["A"])
        verb.affixes.add(affixes["B"])
        verb.affixes.add(affixes["C"])
        # Map the integer prefixes from the old data to the new affix letters
        prefix_map = {1: "D", 2: "E", 3: "F", 4: "G"}
        prefix_numbers = kv["fields"].get("prefixes", [])
        # Get the corresponding Affix objects
        affixes_to_add = [
            affixes[prefix_map[num]] for num in prefix_numbers if num in prefix_map
        ]
        if affixes_to_add:
            verb.affixes.add(*affixes_to_add)


def get_paradigm_objects(kovol_project):
    try:
        verb_paradigm = models.Paradigm.objects.get(
            name="Verb paradigm", project=kovol_project
        )
    except models.Paradigm.DoesNotExist:
        verb_paradigm = models.Paradigm.objects.create(
            name="Verb paradigm",
            project=kovol_project,
            part_of_speech="v",
            row_labels=["1s", "2s", "3s", "1p", "2p", "3p"],
            column_labels=["Past", "Present", "Future"],
        )
    try:
        enclitic = models.Paradigm.objects.get(
            name="Enclitic paradigm", project=kovol_project
        )
    except models.Paradigm.DoesNotExist:
        enclitic = models.Paradigm.objects.create(
            name="Enclitic paradigm",
            project=kovol_project,
            part_of_speech="v",
            row_labels=["1s", "1p", "2s/3s", "2p/3p", "Same actor"],
            column_labels=["Enclitic"],
        )
    try:
        imperatives = models.Paradigm.objects.get(
            name="Imperative paradigm", project=kovol_project
        )
    except models.Paradigm.DoesNotExist:
        imperatives = models.Paradigm.objects.create(
            name="Imperative paradigm",
            project=kovol_project,
            part_of_speech="v",
            row_labels=["Singular", "Plural"],
            column_labels=["Imperative", "Nominalizer", "Perfect"],
        )

    return verb_paradigm, enclitic, imperatives


def import_ignore_words(kovol_project, data):
    for w in data["lexicon.ignoreword"]:
        models.IgnoreWord.objects.create(
            project=kovol_project,
            text=w["fields"]["word"],
            eng=w["fields"]["eng"],
            type=w["fields"]["type"],
            comments=w["fields"]["comments"],
        )


def import_affix_file(kovol_project):
    affix_file = """# hunspell affix file for Kovol by Steve Stanley
# Copyright 2024 Steve Stanley

SET UTF-8

TRY ainlomgestpkubrwdhvyPTMOGHSNYWLBEKfDJIFAVRjU
WORDCHARS -

NOSUGGEST !

# Common spelling mistakes
REP nim neeyim

# The -yam aspect suffix
SFX A Y 1
SFX A 0 yam

# The -i aspect suffix
SFX B Y 1
SFX B 0 i [^aeiou]

# The -a aspect suffix
SFX C Y 1
SFX C 0 a [^aeiou]

# The hi- manner prefix
PFX D Y 1
PFX D 0 hi

# The hi- manner prefix
PFX E Y 1
PFX E 0 ana

# The object prefix
PFX F Y 21
PFX F 0 e [^aieou]
PFX F 0 eng a[nm]
PFX F a e a
PFX F e e e
PFX F i e i
PFX F o e o
PFX F u e u
PFX F 0 no [^aieou]
PFX F 0 nong a
PFX F a no a
PFX F e no e
PFX F i no i
PFX F o no o
PFX F u no u
PFX F 0 n [aieou]
PFX F 0 yog [aeiou]
PFX F 0 yong    a[nm]
PFX F 0 yo [^aeiou]
PFX F 0 wog [aeiou]
PFX F 0 wong a[nm]
PFX F 0 wo [^aeiou]

# The wom- manner prefix
PFX G Y 3
PFX G p womb p
PFX G m wom m
PFX G 0 wom [^pm]

# The -og suffix
SFX H Y 2
SFX H 0 og [^aeiou]
SFX H 0 nog [aeiou]"""
    kovol_project.affix_file = affix_file
    kovol_project.save()


def import_og_suffix(kovol_project, data):
    try:
        affix = models.Affix.objects.get(name="adjectivizer", project=kovol_project)
    except models.Affix.DoesNotExist:
        affix = models.Affix.objects.create(
            name="adjectivizer",
            project=kovol_project,
            applies_to="n",
            affix_letter="H",
        )
    for w in data["lexicon.kovolword"]:
        if not w["fields"]["affixes"]:
            continue
        word = models.LexiconEntry.objects.get(text=w["fields"]["kgu"])
        word.affixes.add(affix)
        word.save()


def import_phrases(kovol_project, data):
    for p in data["lexicon.phraseentry"]:
        pk = p["pk"]
        lexicon_entry = next(
            (
                record
                for record in data["lexicon.lexiconentry"]
                if record.get("pk") == pk
            ),
            None,
        )
        phrase = models.LexiconEntry.objects.create(
            project=kovol_project,
            text=p["fields"]["kgu"],
            pos="ph",
        )

        models.Sense.objects.create(
            entry=phrase,
            eng=lexicon_entry["fields"]["eng"],
            oth_lang=lexicon_entry["fields"]["tpi"],
        )

        if p["fields"]["matat"]:
            models.Variation.objects.create(
                word=phrase,
                type="dialect",
                text=p["fields"]["matat"],
            )


def update_search_index():
    for e in models.LexiconEntry.objects.all():
        update_lexicon_entry_search_field(e.pk)


def __main__():
    log = logging.getLogger("lexicon")
    log.setLevel(logging.ERROR)

    # create or get Kovol project
    try:
        kovol_project = models.LexiconProject.objects.get(language_code="kgu")
    except models.LexiconProject.DoesNotExist:
        kovol_project = models.LexiconProject.objects.create(
            language_name="Kovol",
            language_code="kgu",
            secondary_language="Tok Pisin",
        )

    data = parse_data()
    import_word_data(kovol_project, data)
    import_verb_data(kovol_project, data, log)
    import_ignore_words(kovol_project, data)
    import_affix_file(kovol_project)
    import_og_suffix(kovol_project, data)
    import_phrases(kovol_project, data)
    update_search_index()


if __name__ == "__main__":
    __main__()
    print("Data import completed successfully.")
