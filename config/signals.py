from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
import logging

user_log = logging.getLogger("user_log")


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    user_log.info(
        f"User '{user.username}' (ID: {user.id}) logged out from IP address: {request.META.get('REMOTE_ADDR', 'unknown')}"
    )
