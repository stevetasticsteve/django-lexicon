import logging
import os
import re
from zipfile import ZipFile

from django.http import HttpRequest
from django.urls import reverse
from django.db.models.query import QuerySet

from apps.lexicon import models

log = logging.getLogger("lexicon")
export_folder = os.path.join("data", "exports")


def export_entries(
    file_format: str,
    project: models.LexiconProject,
    checked: bool,
    request: HttpRequest,
) -> str:
    """The view calls this function to export entries in the given format.

    It takes the file format, the project to export from, whether to export only checked entries,
    It returns the path to the created file."""
    check_export_folder()
    match file_format:
        case "dic":
            return create_dic_file(project, checked)
        case "oxt":
            return create_oxt_package(project, checked, request)
        case "xml":
            return create_xml_file(project, checked)


def sanitize_filename_component(value: str) -> str:
    # Only allow alphanumeric, underscore, hyphen
    return re.sub(r"[^a-zA-Z0-9_-]", "_", value)


def check_export_folder() -> None:
    """Checks if the export folder exists, and creates it if not."""
    os.makedirs(export_folder, exist_ok=True)
    if not os.path.isdir(export_folder):
        raise ValueError(f"Export folder {export_folder} is not a directory.")
    elif not os.access(export_folder, os.W_OK):
        raise PermissionError(f"Export folder {export_folder} is not writable.")


def get_entries(
    project: models.LexiconProject, checked: bool
) -> QuerySet:
    """Returns the entries to be exported from the database."""
    if checked:
        return models.LexiconEntry.objects.filter(checked=True, project=project)
    else:
        return models.LexiconEntry.objects.filter(project=project)


def create_dic_file(project: models.LexiconProject, checked: bool) -> str:
    """Creates a new .dic file and returns it's path.

    The path is in the format {lang code}_{version}.dic."""
    safe_lang_code = sanitize_filename_component(project.language_code)
    safe_version = sanitize_filename_component(str(project.version))
    path = os.path.join(export_folder, f"{safe_lang_code}_{safe_version}.dic")
    if not os.path.exists(export_folder):
        os.makedirs(export_folder)

    with open(path, "w") as file:
        entries = get_entries(project, checked)
        file.write(str(len(entries)))
        file.writelines([f"\n{w.tok_ples}" for w in entries])
    return path


def create_xml_file(project: models.LexiconProject, checked: bool) -> str:
    """Creates a new .xml file and returns it's path.

    The path is in the format {lang code}_{version}.xml."""
    safe_lang_code = sanitize_filename_component(project.language_code)
    safe_version = sanitize_filename_component(str(project.version))
    path = os.path.join(export_folder, f"{safe_lang_code}_{safe_version}.xml")
    with open(path, "w") as file:
        entries = get_entries(project, checked)
        file.write('﻿<?xml version="1.0" encoding="utf-8"?>')
        file.write("\n<SpellingStatus>\n")
        for w in entries:
            file.write(f'  <Status Word="{w.tok_ples}" State="R" />\n')
        file.write("</SpellingStatus>")

    return path


def create_oxt_package(
    project: models.LexiconProject, checked: bool, request: HttpRequest
) -> str:
    """Creates a Libre office oxt zip file and returns it's path."""

    entries = get_entries(project, checked)
    dic_contents = str(len(entries)) + "".join([f"\n{w.tok_ples}" for w in entries])

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
    with open(os.path.join(template_path, "description.xml"), "r") as f:
        desc_contents = f.read()
        desc_contents = desc_contents.replace("$VERSION", str(project.version))
        desc_contents = desc_contents.replace("$LANGUAGE_NAME", project.language_name)
        desc_contents = desc_contents.replace("$LANG_CODE", project.language_code)
        desc_contents = desc_contents.replace(
            "$UPDATE_URL",
            request.build_absolute_uri(
                reverse("lexicon:update-oxt", args=[project.language_code])
            ),
        )

    # write dictionaries.xcu file
    with open(os.path.join(template_path, "dictionaries.xcu"), "r") as f:
        xcu_contents = f.read()
        xcu_contents = xcu_contents.replace("$LANG_CODE", project.language_code)

    safe_lang_code = sanitize_filename_component(project.language_code)
    safe_version = sanitize_filename_component(str(project.version))
    zip_path = os.path.join(export_folder, f"{safe_lang_code}_{safe_version}.oxt")
    # Build the zip file
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
