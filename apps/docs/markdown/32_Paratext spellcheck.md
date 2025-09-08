Paratext uses the word list feature to manage spell check in a translation project.

![paratext_wordlist](/static/docs/img/paratext_wordlist.png)

The word list can be built from scratch manually, or use fieldworks data. Helpfully, the information is stored in an .xml file named SpellingStatus.xml.

This file can be downloaded from the lexicon app export page. Once downloaded find the project folder and replace the existing SpellingStatus.xml file with the downloaded one.

![spelling_status](/static/docs/img/spelling_status.png)

Upon restarting Paratext the spelling information will be updated and usable with the spellcheck system. Send/Receive will also send the changes upstream.

Changes made to spelling in the Lexicon app will not automatically be updated in Paratext, a new SpellingStatus.xml file needs to be downloaded. Changes made in Paratext's wordlist will be overwritten whenever the SpellingStatus file is updated meaning **spelling should be managed in the Paratext wordlist or the Lexicon app but not both**.