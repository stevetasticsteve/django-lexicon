from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from apps.lexicon.models import LexiconEntry

@receiver(m2m_changed, sender=LexiconEntry.affixes.through)
@receiver(m2m_changed, sender=LexiconEntry.paradigms.through)
def lexicon_entry_m2m_changed(sender, instance, action, **kwargs):
    """
    Increment project version when affixes are added or removed from a LexiconEntry.
    """
    if action in ["post_add", "post_remove", "post_clear"]:
        instance.project.increment_version()
