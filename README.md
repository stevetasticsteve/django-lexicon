# Lexicon app

An app for centrally managing and then exporting useful formats of a dictionary in a minority language.

# To do
## Features
- An affix system needs to be added. Admins can create an .aff file in the admin and add affix options
- Spelling variations should be added under entries
- Common mispellings for words. To be used for searches in lexicon and to help spelling suggestions in hunspell
- Ignore words. Words to be added to the spell check, but not suggested. For common foreign words.
- The LexiconProject tok ples validator isn't hooked up yet
- Find a way to centrally host .xml and .dic files and have Libre office/word use them. In other words automated updating of spell checks on multiple machines. The oxt extension can define an update url, this should be looked into - updates may be possible using the libre office extension manager.
- A way to automate the updating of a paratext spellingstatus file.

## Performance
- Large projects (like Mibu) have no chance of showing the whole lexicon in 1 page. It has to be paginated somehow. The filter search will need to work with alongside pagination somehow.

## UI
- The header looks off on mobile
- Mobile testing needs to be done
- 2nd language should take the language name from the database in templates

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
- Give the creation of export files to a celery scheduler. Model saves can trigger a scheduled recreation of exports for project. Then when a user clicks download the file doesn't need to be generated on request, it will already exist.
- Be able to export your lexicon project to be imported into a self hosted instance

## Imports
- Import from .csv (spreadsheet)
- Import from .xml (paratext)
- Some way to undo an import. Users may have junk data they don't realise and mix it in with the database, making a huge mess to manually clean up.

## Documentation
- A documentation app should teach users (particularly admins about all the features available
- Deployment documentation. Docker commands, nginx config, env file
