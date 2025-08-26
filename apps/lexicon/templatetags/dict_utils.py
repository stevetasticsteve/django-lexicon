# lexicon/templatetags/dict_utils.py
# These template tags make the conjugation grid view possible.

from django import template

register = template.Library()


@register.filter
def dict_get(d, key):
    """Returns d[key] or empty string if key doesn't exist."""
    if isinstance(d, dict):
        return d.get(key, "")
    return ""


@register.filter
def index(sequence, position):
    """Return the item at the given position in the sequence."""
    try:
        return sequence[position]
    except (IndexError, TypeError):
        return ""
