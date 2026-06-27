# Lexicon app

An app for centrally managing and then exporting useful formats of a dictionary in a minority language.

https://lexicon.reachkovol.com

# To do

4. type checker for adding affixes and paradigms

## Features to implement

- Common misspellings for words. To be used for searches in lexicon and to help spelling suggestions in hunspell
- Find a way to centrally host .xml and .dic files and have Libre office/word use them. In other words automated
  updating of spell checks on multiple machines.
- A way to automate the updating of a paratext spellingstatus file.
- Bulk changes to characters (phonetics -> orthography)

## Bugs

- Pagination doesn't work in main view, htmx request doesn't have pagination info attached.
- When saving a paradigm a button appears for a split second under the grid.
- Paradigms and Affixes are currently __all__. There needs to be filtering to only allow attaching to the correct POS.
- Login rendered in paradigm box on detail page when logged out.
- word variations are not included in EntryDetail page hunspell conjugations

## UI

- The header looks off on mobile
- Mobile testing needs to be done
- 2nd language should take the language name from the database in templates
- Variation form doesn't include notes that are part of the model
- The Affix and Paradigm tables need template work

## Auth

- Password change still using Django default template, despite seeming proper config of custom templates

## Imports

- A legacy .csv import system exists in project code, but is not viewable by users. Current imports are scripted
  manually.

## Testing

- check test coverage

## Management commands

**uv run manage.py backup_projects**
Manually backup all projects to the data/backups folder. Each backup is timestamped. Backups only occur if the version
number has changed.

**uv run manage.py export_project kgu --output kgu_export.json**
Exports the kgu lexicon project to data/kgu_export.json

**uv run manage.py import_project data/kgu_export.json --overwrite**
Imports an exported kgu lexicon. The --overwrite flag deletes the project and imports the file.