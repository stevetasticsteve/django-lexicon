The oxt export options creates a Libre Office extension that:

 - Adds the project language to Libre Office as a language
 - Adds the most recent spellcheck

**Once the oxt is downloaded from the export page the extension can be installed and then subsequently managed with Libre Office's extension manager.**

Open Libre Office extension manager.

![libre_office_menu](/static/docs/img/libre_office_menu.png)

Click add and select the downloaded oxt. Click through the installation steps.

![extension_manager](/static/docs/img/extension_manager.png)

A restart of Libre Office will be required.

![libre_office_restart](/static/docs/img/libre_office_restart.png)

Once restarted the extension is ready. In the bottom panel click on the language selector. Initially, the language will not be a recommended language to select, click more to get the whole list of languages.

![language_selector](/static/docs/img/language_selector.png)

The language will be available using it's 3 letter language code.

![libre_office_language_list](/static/docs/img/libre_office_language_list.png)

Once selected the spellcheck is enabled and can be used. Misspelled words will be underlined in red and right clicking will present a context menu with recommended spellings.

![spellcheck](/static/docs/img/spellcheck.png)

# Updating the extension

Once installed using the extension manager the spellcheck can be updated within Libre Office.

The Lexicon app maintains a version number, visible on the export page. Changes to the lexicon cause the version number to increase. Clicking check for updates will contact the Lexicon app to compare the version numbers. If the lexicon has been an updated Libre Office will be informed that an update is available.

![spellcheck_update](/static/docs/img/spellcheck_update.png)

Clicking install will update to the latest version. **The update mechanism includes hunspell words, checked words only and ignore words.** This default cannot be changed. To use these options download the oxt file from the exports page and install it. The extension can safely be installed on top of itself to update.
