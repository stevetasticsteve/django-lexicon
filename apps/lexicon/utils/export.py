import os
from zipfile import ZipFile

from django.http import request
from django.urls import reverse

from apps.lexicon import models

export_folder = os.path.join("data", "exports")


def export_entries(
    file_format: str, project: models.LexiconProject, checked: bool, request: request
):
    match file_format:
        case "dic":
            return create_dic_file(project, checked)
        case "oxt":
            return create_oxt_package(project, checked, request)
        case "xml":
            return create_xml_file(project, checked)


def get_entries(project: models.LexiconProject, checked: bool):
    if checked:
        return models.LexiconEntry.objects.filter(checked=True, project=project)
    else:
        return models.LexiconEntry.objects.filter(project=project)


def create_dic_file(project: models.LexiconProject, checked: bool) -> str:
    """Creates a new .dic file and returns it's path.

    The path is in the format <lang code>_version.dic."""
    path = os.path.join(export_folder, f"{project.language_code}_{project.version}.dic")

    with open(path, "w") as file:
        entries = get_entries(project, checked)
        file.write(str(len(entries)))
        file.writelines([f"\n{w.tok_ples}" for w in entries])
    return path


def create_xml_file(project: models.LexiconProject, checked: bool) -> str:
    """Creates a new .xml file and returns it's path.

    The path is in the format <lang code>_version.xml."""
    path = os.path.join(export_folder, f"{project.language_code}_{project.version}.xml")
    with open(path, "w") as file:
        entries = get_entries(project, checked)
        file.write('﻿<?xml version="1.0" encoding="utf-8"?>')
        file.write("\n<SpellingStatus>\n")
        for w in entries:
            file.write(f'  <Status Word="{w.tok_ples}" State="R" />\n')
        file.write("</SpellingStatus>")

    return path


def create_oxt_package(
    project: models.LexiconProject, checked: bool, request: request
) -> str:
    """Creates a Libre office oxt zip file and returns it's path."""

    entries = get_entries(project, checked)
    dic_contents = str(len(entries)) + "".join([f"\n{w.tok_ples}" for w in entries])

    template_path = os.path.join("apps", "lexicon", "templates", "oxt")

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

    zip_path = os.path.join(
        export_folder, f"{project.language_code}_{project.version}.oxt"
    )
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
