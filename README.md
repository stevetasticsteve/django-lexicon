# Lexicon app

An app for centrally managing and then exporting useful formats of a dictionary in a minority language.

https://dev.codebysteve.com

# To do

3. Project edit permissions
   1. Project model views
   2. Variation model
   3. Ignore model
   4. Paradigm views (responds with htmx 403, not visible on template)
   6. Affix views (responds with htmx 403, not visible on template)
4. registration system
5. Showing Hunspell constructed words in detail view
6. 403.html not showing

## Features to implement
- Common misspellings for words. To be used for searches in lexicon and to help spelling suggestions in hunspell
- Find a way to centrally host .xml and .dic files and have Libre office/word use them. In other words automated updating of spell checks on multiple machines.
- The oxt extension can define an update url. A http endpoint has been defined that correctly returns an xml with update information. Libre office can now see that there are updates for the extension, but can't download it.
- A way to automate the updating of a paratext spellingstatus file.
- Backup and export of projects. Allow project admins to rollback
- Bulk changes to characters (phonetics -> orthography)
- Feedback form
- User documentation throughout site

## Deployment
- 
  
## Bugs
- Libre office can contact the update server and see updated oxt packages, but downloading them fails.
- The save method on the models that updates the version number should only change if the tok ples changes, and it should only go up a single version number on import
- Pagination doesn't work in main view, htmx request doesn't have pagination info attached.
- When saving a paradigm a button appears for a split second under the grid.
- Paradigms and Affixes are currently __all__. There needs to be filtering to only allow attaching to the correct POS.

## UI
- The header looks off on mobile
- Mobile testing needs to be done
- 2nd language should take the language name from the database in templates
- Variation form doesn't include notes that are part of the model
- The Affix and Paradigm tables need template work

## Auth
- Password change requires templates
- templates/registration/password_change_form.html
- templates/registration/password_change_done.html
- sign up form. Need a registration app
- password reset functionality
- Different users need roles. You should only be able to edit pages you have permission to
- Eventually use office 365 logins and have integration with member services

## Exports
- Clean up of created exports
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

## Logging
- 
