The lexicon app can use [Hunspell](https://hunspell.github.io/) to automatically create conjugations of words with predictable affixes. The automatic conjugations can be included in exported spellchecks.

In Kovol for example the e- prefix can be added as an indirect object to the verb wendege and the -yam continuous aspect suffix can also be added. The combinations then become:

 - wendege
 - ewendege
 - wendegeyam
 - ewendegeyam

The two affixes create 4 word forms that all need to be included in a spellcheck.

The affix system in the lexicon app makes it possible to assign the e- and -yam affixes to the wendege entry and then hunspell rules can be created to automatically conjugate (and spell check) the word forms.

## Adding affix information to words
First of all an affix needs to be created for the project. In the project admin follow the link to affixes and create a new affix. We will assign the letter A to the -yam affix. Hunspell will refer to it as affix A.

![affix_list](/static/docs/img/affix_list.png)

We give the affix a name so we can recognize it, restrict the types of entries it can apply to (nouns or verbs for example) and the assign it an arbitrary letter. No conjugations rules are supplied at this point.

Now we find the entry for wendege and scroll down to the affixes. Since we defined the -yam affix to apply to verbs it will be available as an option. We can assign the affix to the word.

![wendege_affixes](/static/docs/img/wendege_affixes.png)

This step associates the lexicon entry wendege with the A affix. Nothing happens at this stage as we haven't defined hunspell rules for affix A.

## Defining affix rules
The next step is to edit our affix rules to describe how the A affix should behave. In the project admin follow the link to the affix file. A pair of text boxes are displayed.

![affix_file_blank](/static/docs/img/affix_file_empty.png)


The right box is the project's current affix file. The affix file defines the automatic conjugation rules. Editing this text and hitting save will save changes to the affix file.

We remember that the -yam affix has letter A, so we'll write rules for affix A with the following 3 lines.

---


`\# The -yam aspect suffix`


`SFX A Y 1`


`SFX A 0 yam`

---

Line 1 is a comment. We can start the line with a # and then write whatever we wish to help ourselves and our team mates read the affix file.

Line 2 states **SFX** (this word is a SFX) **A** (This rule is for affix A) **Y** (This affix can be combined with others) **1** (The following 1 line has the rules for A)

Line 3 states **SFX** (this word is a SFX) **A** (This rule is for affix A) **0** (There is no character stripping) **yam** (yam is the suffix form)

We can now test the affix generation. In the box on the left we write

---


`wendege/A`


`libige`


---

We provide two words for testing, wendege and libige. We mark wendege as accepting the A affix with /A. Libige doesn't recieve the affix. Wit the generate button the hunspell rules are applied and conjugations are shown.

![affix_generation](/static/docs/img/affix_generation.png)

You'll see that the hunspell rules were correctly applied. If we save the affix file so that we now have rules for affix A, and we return to the entry for wendege we'll see that the automatic conjugations are shown at the bottom. All words marked as accepting the A affix will also conjugate automatically.

By writing hunspell rules it is possible for hundreds of conjugations per word to be generated automatically in a hunspell spell checker (like used in Libre Office). The resulting size of the lexicon and spellcheck file is massively reduced by taking advantage of this. If a spelling change needs to be made to wendege we don't have to manually correct hundreds of conjugations we manually wrote out, simply update the entry once and hunspell will conjugate the rest.

Hunspell rules can quite complex and can handle conditions and allomorphs. See [Writing hunspell affixes](/docs/22_Writing hunspell rules)
