from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Transaction, MarketplaceListing, MarketplaceNotification
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

@receiver(post_save, sender=MarketplaceListing)
def create_marketplace_notifications(sender, instance, created, **kwargs):
    """Create notifications for marketplace events."""
    if not created and instance.status == 'sold':
        # Notify seller if they have marketplace notifications enabled
        if instance.seller.notification_preferences.marketplace_notifications:
            MarketplaceNotification.objects.create(
                user=instance.seller,
                listing=instance,
                notification_type='listing_sold'
            )
        
        # Notify buyer if they have marketplace notifications enabled
        if instance.buyer and instance.buyer.notification_preferences.marketplace_notifications:
            MarketplaceNotification.objects.create(
                user=instance.buyer,
                listing=instance,
                notification_type='purchase_successful'
            )
    
    elif not created and instance.status == 'cancelled':
        # Only notify if user has marketplace notifications enabled
        if instance.seller.notification_preferences.marketplace_notifications:
            MarketplaceNotification.objects.create(
                user=instance.seller,
                listing=instance,
                notification_type='listing_cancelled'
            ) 