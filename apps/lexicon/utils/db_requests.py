# These utils provide some common database queries used by templates


def group_lexicon_entries_by_letter(entries: list) -> dict:
    """Gives a dict of initial letters as keys and the lexicon entries as values."""
    # Get the 1st letter of the tok ples and create a set
    letters = set([str(w.tok_ples)[0] for w in entries])
    # Use a dict comprehension to build {"a": Abus Lexicon entry}
    lexicon = {
        letter: [w for w in entries if w.tok_ples[0] == letter] for letter in letters
    }
    return dict(sorted(lexicon.items()))
