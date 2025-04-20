from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import TradeOffer, TradeHistory, TradeNotification
from messaging.models import Message

@receiver(post_save, sender=TradeOffer)
def create_trade_notifications(sender, instance, created, **kwargs):
    """Create notifications when a trade offer is created or updated."""
    if created:
        # Notify recipient of new trade offer
        TradeNotification.objects.create(
            user=instance.recipient,
            trade_offer=instance,
            notification_type='offer_received'
        )
        
        # Send a message to the recipient
        Message.objects.create(
            sender=instance.sender,
            recipient=instance.recipient,
            subject=f"New Trade Offer from {instance.sender.username}",
            content=f"{instance.sender.username} has offered you a trade. Check your trade offers to respond."
        )
    else:
        # Handle status changes
        if instance.status == 'accepted':
            # Notify sender that their offer was accepted
            TradeNotification.objects.create(
                user=instance.sender,
                trade_offer=instance,
                notification_type='offer_accepted'
            )
            
            # Create trade history record
            TradeHistory.objects.create(
                trade_offer=instance,
                status='completed'
            )
            
            # Send messages to both parties
            Message.objects.create(
                sender=instance.recipient,
                recipient=instance.sender,
                subject="Trade Accepted",
                content=f"{instance.recipient.username} has accepted your trade offer."
            )
            
        elif instance.status == 'declined':
            # Notify sender that their offer was declined
            TradeNotification.objects.create(
                user=instance.sender,
                trade_offer=instance,
                notification_type='offer_declined'
            )
            
            # Create trade history record
            TradeHistory.objects.create(
                trade_offer=instance,
                status='declined'
            )
            
            # Send message to sender
            Message.objects.create(
                sender=instance.recipient,
                recipient=instance.sender,
                subject="Trade Declined",
                content=f"{instance.recipient.username} has declined your trade offer."
            )
            
        elif instance.status == 'cancelled':
            # Notify both parties
            for user in [instance.sender, instance.recipient]:
                TradeNotification.objects.create(
                    user=user,
                    trade_offer=instance,
                    notification_type='trade_cancelled'
                )
            
            # Create trade history record
            TradeHistory.objects.create(
                trade_offer=instance,
                status='cancelled'
            )
            
            # Send messages to both parties
            Message.objects.create(
                sender=instance.sender,
                recipient=instance.recipient,
                subject="Trade Cancelled",
                content=f"{instance.sender.username} has cancelled the trade offer."
            )

@receiver(pre_save, sender=TradeOffer)
def handle_trade_completion(sender, instance, **kwargs):
    """Handle the actual Pokémon transfer when a trade is completed."""
    if instance.status == 'accepted' and instance.pk:
        try:
            old_instance = TradeOffer.objects.get(pk=instance.pk)
            if old_instance.status != 'accepted':
                # Transfer Pokémon from sender to recipient
                for pokemon in instance.offered_pokemon.all():
                    pokemon.user = instance.recipient
                    pokemon.save()
                
                # Transfer Pokémon from recipient to sender
                for pokemon in instance.requested_pokemon.all():
                    pokemon.user = instance.sender
                    pokemon.save()
        except TradeOffer.DoesNotExist:
            pass 