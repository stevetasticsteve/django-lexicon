# Lexicon app

An app for centrally managing and then exporting useful formats of a dictionary in a minority language.

https://lexicon.reachkovol.com

# To do
4. type checker for adding affixes and paradigms
6. per project backup

## Features to implement
- Common misspellings for words. To be used for searches in lexicon and to help spelling suggestions in hunspell
- Find a way to centrally host .xml and .dic files and have Libre office/word use them. In other words automated updating of spell checks on multiple machines.
- A way to automate the updating of a paratext spellingstatus file.
- Backup and export of projects. Allow project admins to rollback
- Bulk changes to characters (phonetics -> orthography)

  
## Bugs
- The save method on the models that updates the version number should only change if the tok ples changes, and it should only go up a single version number on import
- Pagination doesn't work in main view, htmx request doesn't have pagination info attached.
- When saving a paradigm a button appears for a split second under the grid.
- Paradigms and Affixes are currently __all__. There needs to be filtering to only allow attaching to the correct POS.
- Login rendered in paradigm box on detail page when logged out.
- If no affixes are set for the project there shouldn't be the option to add them to a word on the detail page
- word variations are not included in EntryDetail page hunspell conjugations

## UI
- The header looks off on mobile
- Mobile testing needs to be done
- 2nd language should take the language name from the database in templates
- Variation form doesn't include notes that are part of the model
- The Affix and Paradigm tables need template work

## Auth
- Password change still using Django default template, despite seeming proper config of custom templates

## Exports
- Currently exports are located inside the running container. This won't work for round robin load sharing, a volume needs to be mapped.
- Give the creation of export files to a celery scheduler. Model saves can trigger a scheduled recreation of exports for project. Then when a user clicks download the file doesn't need to be generated on request, it will already exist.
- Be able to export your lexicon project to be imported into a self hosted instance

## Imports
- Import from .csv (spreadsheet)
- Import from .xml (paratext)
- Some way to undo an import. Users may have junk data they don't realise and mix it in with the database, making a huge mess to manually clean up.
- Imports currently accept any file and it'd be easy to cause an error
- Imports need to take the username who requested the import and add that to the database to avoid None.
- Users can exceed the database's max length restrictions. Currently on csv import this is passed over. Need to truncate the strings before adding them to the db.


## Testing
- check test coverage
