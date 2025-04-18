from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message
from django.core.mail import send_mail
from django.conf import settings

@receiver(post_save, sender=Message)
def notify_new_message(sender, instance, created, **kwargs):
    """
    Send a notification when a new message is created
    """
    if created:
        # Here you could implement email notifications, push notifications, etc.
        # For now we'll just print to console for debugging
        print(f"New message from {instance.sender} to {instance.recipient}: {instance.content[:50]}...") 