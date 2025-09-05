The [hunspell rules](https://www.systutorials.com/docs/linux/man/4-hunspell/) can make affixes quite adaptable. Let's create a simple prefix and make it more complex. We'll invent a re- prefix to attach to different words.

We'll use the invented words:

 - do
 - mo
 - da

We want the conjugations:

- womdo
- womo (not womdo, there is a reduction when two C come together)
- wamda (not womda, the vowel in the prefix assimilates )

---


`PFX A Y 1`


`PFX A 0 wom`

---

Now if we test if with an invented word "do", which would be do/A, we get do and womdo. Now imagine we have the word mo, hunpsell would generate wommo.

We can update our affix file like this:

---


`PFX A Y 2`

`PFX A 0 wom [^m]`

`PFX A m wom [m]`

---

We need to

 - Update the first line from 1 to 2, as we now have 2 lines of PFX rules
 - Make the first line conditional [^m] means "only when not before m"
 - Make the second line conditional [m] means "only when before m
 - Add m as a stripping character to line 2, telling it to strip m's from the root

This will cause it to conjugate womo and not wommo.

Next we can add another rule for changing the vowel in the prefix when there is an "a" in the root:

`PFX A Y 3`

`PFX A 0 wom [^m][^a]`

`PFX A m wom [m]`

`PFX A m wam [\d*]a`

In this case we update the rules so that line one applies to roots of [^m][^a] "any character not m and then any character not a"
Then line 3 applies to [\d]*a "one or more of any character followed by a".

Note line 3 would also match "dada", so you may need to tweak your conditions, but it will work for our simple example.

Ask for help from an AI LLM like chatGPT to help you tweak your affix file.


## Pattern Matching in Conditions

The "regex-like" patterns in Hunspell affix files are primarily used in the condition part of SFX (suffix) rules. They specify what the stem must end with for the affix to be applied.

Here are the key elements you'll find:

    Literal Characters: Any character that isn't a special symbol is treated literally. For example, ed would match stems ending in "ed".

    ^ (Caret): Matches the beginning of the word.

        Example: ^co in a condition would mean the stem must start with "co".

    $ (Dollar Sign): Matches the end of the word.

        Example: y$ would mean the stem must end with "y".

    . (Dot): Matches any single character.

        Example: . in a condition means the stem can end with any character.

    [...] (Character Sets): Matches any single character within the brackets.

        Example: [^y] means the stem must end with any character except "y".

        Example: [aeiou] means the stem must end with a vowel.

    * (Asterisk): Matches zero or more occurrences of the preceding character or character set.

        Example: a* means zero or more "a"s. ba*t would match "bt", "bat", "baat", etc.

    ? (Question Mark): Matches zero or one occurrence of the preceding character or character set.

        Example: colou?r would match "color" and "colour".

Important Note: These are not full regular expressions as found in programming languages. Hunspell's pattern matching is more limited and specifically designed for its affix rule system. For instance, you won't find features like lookarounds, complex quantifiers, or grouping with parentheses in the same way.
