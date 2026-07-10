# Advanced searches

Advanced searches uses regex ("regular expression") to allow you search for **patterns** in a word, not just exact text.
This is useful for
questions like "which words end in *-ind* or *-end*?" or "which words start with a vowel?" — questions a plain text
search can't answer.

Toggle the **Advanced search** checkbox next to the search box to switch to pattern search. It works with both the
project
language and English toggle.

## The basics

Searches are case insensitve

**position**

- `^` means start of a word.
    - `^wa` matches wagam, wala - but not libuwa

- `$` means end of a word
    - `$nd` matches libigond, tobogond - but not pigondyam

**characters**

- `.` means any character
- `\s` means any whitespace character
- `\S` means any non whitespace character
- `\w` means any word character (a-z, 0-9)
- `\W` means any non word character

**patterns and groups**

- `[abc]` matches a or b or c
- `[^abc]` matches not a or b or c
- `(ga)` is a group and matches ga
- `(ga)*` matches zero or more of the group ga
- `(ga)+` matches one or more of the group ga
- `(ga){3}` matches three group ga

## Common searches for language analysis

**Words ending in a particular sequence** — useful for spotting a suffix pattern:

```
ind$
```

Matches any word ending in *-ind*

**Words ending in one of several variants** — e.g. checking whether a suffix has multiple surface forms:

```
[ie]nd$
```

Matches words ending in either *-ind* or *-end*.

**Words starting with a vowel:**

```
^[aeiou]
```

**Words containing a doubled vowel** (useful for spotting vowel length or reduplication):

**Words of an exact length** — e.g. all 3-letter words:

```
^...$
```

Each `.` is one character, so three dots between `^` and `$` matches exactly three characters.

**Words matching a shape** — e.g. consonant-vowel-consonant-vowel:

```
^[^aeiou][aeiou][^aeiou][aeiou]$
```

## Searching English glosses with regex

Toggle **English** and **Regex** together to run pattern searches over the English sense glosses instead of the project
language. For example, `^to [a-z]+$` would find glosses that are exactly a two-word verb phrase starting with "to".

## Things to know

- **Invalid patterns are rejected safely.** If you mistype a pattern (e.g. leave a bracket unclosed, like `[ind`),
  you'll see an error message rather than results — fix the pattern and the search will re-run automatically.
- **Long patterns aren't allowed.** Patterns are capped at 150 characters. This is far more than any real search
  needs, and exists mainly to keep the search fast for everyone.
- **No backreferences.** As above, patterns like `\1` (referring back to an earlier match) aren't supported by the
  underlying database engine. Most linguistic search needs — endings, beginnings, character classes, alternation — don't
  need this. If you find yourself wanting it, it's a sign you may want a dedicated report instead — ask on
  the [feedback page](/feedback/).
- **This isn't quite the same regex dialect as Python or Perl.** For everyday searches (endings, character classes,
  alternation, anchors) it behaves identically to what you'd expect. A few obscure features differ; if something you'd
  expect to work doesn't, mention it on the [feedback page](/feedback/) and it can be looked into.
- **Google search regex** to learn more.