## What is the lexicon app?
The lexicon app is a way for a team to manage centrally **manage a lexicon and export spellcheck** for a minority language.
It's main features are:

 - **Built for team collaboration.** The underlying system is designed to allow multiple users to maintain and add to the project.

 - **Check and review system.** Building a lexicon for a minority language is a messy process, mark words as being checked to indicate the spelling has been confirmed and use the review system to flag words that need more study.
 
 - **Flexible paradigm grids** can be created to visually represent conjugations of words.
 
 - **Record spelling and dialect variations** of words.
 
 - **Hunspell integration** - automatic conjugation of predictable affixation.
  
 - **Export into useful spellcheck formats.** Enables spellcheck in Libre Office and Paratext.
  
## Why was the lexicon app created?
While learning the Kovol language of Papua New Guinea the team started an Excel spreadsheet to record dictionary data. This worked for a while, but the team experienced sync issues sharing the spreadsheet, repeated words and difficulty expressing conjugation and affix information.

To solve this problem the lexicon app was developed to replace the spreadsheet. Using Django and Postgres meant that the sync issues were a thing of the past. The Kovol verb paradigms could be represented nicely in a single view.

The Kovol team used this app over the next 2 years to manage their lexicon. The team found it to be a useful tool for consolidating their spelling. The spellcheck export for Libre Office and Paratext has meant that literacy and translation projects have benefitted by the team using spellcheck.