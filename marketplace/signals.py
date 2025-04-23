from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Transaction
from messaging.models import Message

@receiver(post_save, sender=Transaction)
def send_transaction_messages(sender, instance, created, **kwargs):
    """
    Send messages to both buyer and seller when a transaction is completed
    """
    if created:
        # Message to seller
        Message.objects.create(
            sender=instance.buyer,
            recipient=instance.listing.seller,
            subject=f"Your {instance.listing.pokemon.card.name} has been sold!",
            content=f"{instance.buyer.username} has purchased your {instance.listing.pokemon.card.name} for {instance.price_paid} coins."
        )
        
        # Message to buyer
        Message.objects.create(
            sender=instance.listing.seller,
            recipient=instance.buyer,
            subject=f"Purchase of {instance.listing.pokemon.card.name} successful!",
            content=f"You have successfully purchased {instance.listing.pokemon.card.name} from {instance.listing.seller.username} for {instance.price_paid} coins."
        ) 