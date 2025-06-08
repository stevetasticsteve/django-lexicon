import logging

from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.lexicon.models import Conjugation, LexiconEntry, Variation
from apps.lexicon.tasks import update_lexicon_entry_search_field

log = logging.getLogger("lexicon")


@receiver(post_save, sender=LexiconEntry)
@receiver(post_save, sender=Variation)
@receiver(post_save, sender=Conjugation)
def trigger_search_field_update(sender, instance, **kwargs):
    log.debug("Triggering search field update")
    # Determine the LexiconEntry to update
    if isinstance(instance, LexiconEntry):
        entry_pk = instance.pk
    elif isinstance(instance, (Variation, Conjugation)):
        entry_pk = instance.word.pk  # Assuming 'word' is the ForeignKey to LexiconEntry

    # Ensure the task runs only after the transaction commits
    transaction.on_commit(lambda: update_lexicon_entry_search_field.delay(entry_pk))


# You might also want to handle deletions if a deleted item should remove its text from the search field
@receiver(post_delete, sender=Variation)
@receiver(post_delete, sender=Conjugation)
def trigger_search_field_update_on_delete(sender, instance, **kwargs):
    log.debug("Triggering search field update on delete")
    # Ensure the task runs only after the transaction commits)
    transaction.on_commit(
        lambda: update_lexicon_entry_search_field.delay(instance.word.pk)
    )
