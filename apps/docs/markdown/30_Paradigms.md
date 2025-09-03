## How to use the paradigm system
The paradigm system can be used to display conjugations for a word in a grid. In the Kovol language verbs have different endings for the actor and tense. The verb libinim can thus have 18 different conjugations.

The paradigm system enables these to be displayed in a table.

First in the project admin go the paradigms page and create a new paradigm. For our Kovol paradigm we want the columns to read past, present and future. We want our rows to read 1s, 2s, 3s, 1p, 2p, 3p to represent 1 singular, 2 singular etc.
What we name the rows and columns is flexible. We do want to ensure that we mark it as applies to verbs though.

![kovol paradigm setup](/static/docs/img/kovol_paradigm_setup.png)

We then go to our libinim entry. We click on "add a paradigm".

![libinim](/static/docs/img/libinim.png)

In the modal that pops up we add the paradigm we just created:

![libinim](/static/docs/img/libinim_add_paradigm.png)

Once we have done this the paradigm is associated with the lexicon entry. A conjugations area will appear on the entry's page and we can edit the conjugations as we need to.

![libinim](/static/docs/img/libinim_conjugations.png)

All of the conjugations included in this grid will be exported into the spellcheck. All the conjugations will also combine with Hunspell affixes.

## When to use the paradigm system
The paradigm system is best used:

1. With grammatically unpredictable words (irregular)
2. When a grid display is desired

If conjugations are 100% predictable they can all be conjugated automatically with hunspell, whereas paradigm grids need to be manually filled in.
Kovol verbs are mostly predictable with their conjugations, but not entirely, thus the Kovol team chose the paradigm grid system for storing conjugations.