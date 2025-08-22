import logging
import os
import re
from zipfile import ZipFile

from django.http import HttpRequest
from django.urls import reverse

from apps.lexicon import models
from apps.lexicon.utils.hunspell import unmunch

log = logging.getLogger("lexicon")
export_folder = os.path.join("data", "exports")


# Main callable function for exporting entries.
def export_entries(
    file_format: str,
    project: models.LexiconProject,
    request: HttpRequest,
    checked: bool = True,
    hunspell: bool = True,
    ignore_word_flag: bool = True,
) -> str:
    """The view calls this function to export entries in the given format.

    It takes the file format, the project to export from, whether to export only checked entries,
    It returns the path to the created file."""
    _check_export_folder()
    match file_format:
        case "dic":
            return _create_dic_file(
                project,
                checked=checked,
                hunspell=hunspell,
                ignore_word_flag=ignore_word_flag,
            )
        case "oxt":
            return _create_oxt_package(
                project,
                request,
                checked=checked,
                hunspell=hunspell,
                ignore_word_flag=ignore_word_flag,
            )
        case "xml":
            return _create_xml_file(
                project,
                checked=checked,
                hunspell=hunspell,
                ignore_word_flag=ignore_word_flag,
            )


# Helper functions for creating file names and paths.
def _sanitize_filename_component(value: str) -> str:
    # Only allow alphanumeric, underscore, hyphen
    return re.sub(r"[^a-zA-Z0-9_-]", "_", value)


def _check_export_folder() -> None:
    """Checks if the export folder exists, and creates it if not."""
    os.makedirs(export_folder, exist_ok=True)
    if not os.path.isdir(export_folder):
        raise ValueError(f"Export folder {export_folder} is not a directory.")
    elif not os.access(export_folder, os.W_OK):
        raise PermissionError(f"Export folder {export_folder} is not writable.")


def _get_export_path(project, extension: str) -> str:
    safe_lang_code = _sanitize_filename_component(project.language_code)
    safe_version = _sanitize_filename_component(str(project.version))
    return os.path.join(export_folder, f"{safe_lang_code}_{safe_version}.{extension}")


# Helper functions for retrieving export content from the database.
def _get_word_list(
    project: models.LexiconProject,
    checked: bool = True,
    hunspell: bool = True,
    ignore_word_flag: bool = True,
) -> list:
    """Returns the entries to be exported from the database."""
    base_query = models.LexiconEntry.objects.filter(project=project)

    if checked:
        base_query = base_query.filter(checked=True)

    # Use prefetch_related to grab all related objects efficiently
    entries = base_query.prefetch_related("affixes", "conjugations", "variations")

    word_list = []
    for entry in entries:
        # gather all the related model data
        affix_letters = "".join(a.affix_letter for a in entry.affixes.all())
        conjugation_objects = entry.conjugations.all()
        variation_objects = entry.variations.filter(included_in_spellcheck=True)

        # If hunspell is enabled, append the affix letters to the word and conjugations
        if hunspell and affix_letters:
            base_word = f"{entry.text}/{affix_letters}"
            conjugations = (
                f"{c.conjugation}/{affix_letters}" for c in conjugation_objects
            )
            variations = (f"{v.text}/{affix_letters}" for v in variation_objects)
        else:
            base_word = entry.text
            conjugations = (c.conjugation for c in conjugation_objects)
            variations = (v.text for v in variation_objects)

        # Add all generated words and their forms to the main list
        word_list.append(base_word)
        word_list.extend(conjugations)
        word_list.extend(variations)

    # Process and add ignore words after the main loop
    if ignore_word_flag:
        ignore_word_list = models.IgnoreWord.objects.filter(project=project)
        # Use a list comprehension to build the new list of strings with the "ignoreme/!" suffix
        if hunspell:
            ignore_words_formatted = [f"{w.text}/!" for w in ignore_word_list]
        else:
            ignore_words_formatted = [w.text for w in ignore_word_list]
        word_list.extend(ignore_words_formatted)
    return word_list


# Helper functions that format the export content.
def _create_dic_oxt_string(
    project: models.LexiconProject, checked=True, hunspell=True, ignore_word_flag=True
) -> str:
    """
    Queries the database for Entries and creates a string for a .dic file suitable for an oxt.

    This function generates a string suitable for a Hunspell .dic file, including
    entries, conjugations, and variations, with optional Hunspell affix flags.

    Args:
        project (models.LexiconProject): The project to query for entries.
        checked (bool, optional): If True, only include checked entries. Defaults to True.
        hunspell (bool, optional): If True, append Hunspell affix flags. Defaults to True.

    Returns:
        str: A newline-separated string formatted for a .dic file.
    """
    word_list = _get_word_list(project, checked, hunspell, ignore_word_flag)
    word_list.insert(0, str(len(word_list)))

    return "\n".join(word_list)


def _create_xml_string(
    project: models.LexiconProject, checked=True, hunspell=True, ignore_word_flag=True
) -> str:
    """Returns a .xml string to be used in .xml file.

    Args:
        project (models.LexiconProject): The project to query for entries.
        checked (bool, optional): If True, only include checked entries. Defaults to True.
        hunspell (bool, optional): If True, append Hunspell affix flags. Defaults to True.

    Returns:
        str: A newline-separated string formatted for a .xml file."""
    words = _create_dic_string(
        project, checked=checked, hunspell=hunspell, ignore_word_flag=ignore_word_flag
    )
    words = words.split("\n")[1:]  # skip the first line with the count

    xml_lines = ['<?xml version="1.0" encoding="utf-8"?>', "<SpellingStatus>"]
    for w in words:
        xml_lines.append(f'  <Status Word="{w}" State="R" />')
    xml_lines.append("</SpellingStatus>")

    return "\n".join(xml_lines)


def _create_dic_string(
    project: models.LexiconProject, checked=True, hunspell=True, ignore_word_flag=True
) -> str:
    """Returns a plain .dic string to be used in a plain .dic file.

    A .dic file outside of hunspell needs to be unmunched to build all affix conjugations.

    Args:
        project (models.LexiconProject): The project to query for entries.
        checked (bool, optional): If True, only include checked entries. Defaults to True.
        hunspell (bool, optional): If True, append Hunspell affix flags. Defaults to True.

    Returns:
        str: A newline-separated string formatted for a .dic file."""

    if hunspell:
        word_list = unmunch(
            _create_dic_oxt_string(
                project,
                checked=checked,
                hunspell=hunspell,
                ignore_word_flag=ignore_word_flag,
            ),
            project.affix_file,
        )
    else:
        word_list = _get_word_list(
            project, checked=checked, hunspell=False, ignore_word_flag=ignore_word_flag
        )

    word_list.insert(0, str(len(word_list)))
    return "\n".join(word_list)


# Helper functions that create the actual export files and return their paths.
def _create_dic_file(
    project: models.LexiconProject, checked=True, hunspell=True, ignore_word_flag=True
) -> str:
    """Creates a new .dic file and returns it's path.

    The path is in the format {lang code}_{version}.dic."""

    path = _get_export_path(project, "dic")

    dic_string = _create_dic_string(
        project, checked=checked, hunspell=hunspell, ignore_word_flag=ignore_word_flag
    )
    try:
        with open(path, "w", encoding="utf-8") as file:
            file.write(dic_string)
        return path

    except IOError as e:
        log.error(f"Failed to write file {path}: {e}")
        raise


def _create_xml_file(
    project: models.LexiconProject,
    checked: bool = True,
    hunspell: bool = True,
    ignore_word_flag: bool = True,
) -> str:
    """Creates a new .xml file and returns it's path.

    The path is in the format {lang ruff checcode}_{version}.xml."""
    path = _get_export_path(project, "xml")
    try:
        with open(path, "w", encoding="utf-8") as file:
            file.write(
                _create_xml_string(
                    project,
                    checked=checked,
                    hunspell=hunspell,
                    ignore_word_flag=ignore_word_flag,
                )
            )
        return path
    except IOError as e:
        log.error(f"Failed to write file {path}: {e}")
        raise


def _create_oxt_package(
    project: models.LexiconProject,
    request: HttpRequest,
    checked: bool,
    hunspell: bool,
    ignore_word_flag: bool,
) -> str:
    """Creates a Libre office oxt zip file and returns it's path."""

    dic_contents = _create_dic_oxt_string(
        project, checked=checked, hunspell=hunspell, ignore_word_flag=ignore_word_flag
    )

    template_path = os.path.join("apps", "lexicon", "templates", "oxt")
    if not os.path.exists(template_path):
        raise FileNotFoundError(
            f"Template path {template_path} does not exist. "
            "Please ensure the template files are present."
        )

    # Iterate over files within the directory
    for filename in os.listdir(template_path):
        file_full_path = os.path.join(template_path, filename)
        if not os.path.exists(file_full_path):
            raise FileNotFoundError(f"Template file {file_full_path} does not exist.")
        if not os.access(file_full_path, os.R_OK):
            raise PermissionError(f"Template file {file_full_path} is not readable.")

    # write the description xml
    try:
        path = os.path.join(template_path, "description.xml")
        with open(path, "r", encoding="utf-8") as f:
            desc_contents = f.read()
            desc_contents = desc_contents.replace("$VERSION", str(project.version))
            desc_contents = desc_contents.replace(
                "$LANGUAGE_NAME", project.language_name
            )
            desc_contents = desc_contents.replace("$LANG_CODE", project.language_code)
            desc_contents = desc_contents.replace(
                "$UPDATE_URL",
                request.build_absolute_uri(
                    reverse("lexicon:update_oxt", args=[project.language_code])
                ),
            )
    except IOError as e:
        log.error(f"Failed to read file {path}: {e}")
        raise

    # write dictionaries.xcu file
    try:
        path = os.path.join(template_path, "dictionaries.xcu")
        with open(path, "r", encoding="utf-8") as f:
            xcu_contents = f.read()
            xcu_contents = xcu_contents.replace("$LANG_CODE", project.language_code)
    except IOError as e:
        log.error(f"Failed to read file {path}: {e}")
        raise

    zip_path = _get_export_path(project, "oxt")
    # Build the zip file
    try:
        with ZipFile(
            zip_path,
            "w",
        ) as myzip:
            # write the .dic
            myzip.writestr(
                os.path.join("dictionaries", f"{project.language_code}_PG.dic"),
                dic_contents,
            )
            # write the .add
            myzip.writestr(
                os.path.join("dictionaries", f"{project.language_code}_PG.aff"),
                project.affix_file,
            )
            # write the other files
            myzip.writestr("dictionaries.xcu", xcu_contents)
            myzip.writestr("description.xml", desc_contents)
            myzip.write(os.path.join(template_path, "License.txt"), "License.txt")
            myzip.write(
                os.path.join(template_path, "manifest.xml"),
                os.path.join("META-INF", "manifest.xml"),
            )

        return zip_path
    except IOError as e:
        log.error(f"Failed to write file {zip_path}: {e}")
        raise
