from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from pokemon.models import UserPokemon

class TradeOffer(models.Model):
    """Represents a trade proposal between two users."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_trade_offers',
        help_text="User who initiated the trade"
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_trade_offers',
        help_text="User who received the trade offer",
        null=True,
        blank=True
    )
    
    offered_pokemon = models.ManyToManyField(
        UserPokemon,
        related_name='offered_in_trades',
        help_text="Pokémon being offered by the sender"
    )
    requested_pokemon = models.ManyToManyField(
        UserPokemon,
        related_name='requested_in_trades',
        help_text="Pokémon being requested from the recipient"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of the trade offer"
    )
    
    message = models.TextField(
        blank=True,
        help_text="Optional message from the sender"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sender', 'status']),
            models.Index(fields=['recipient', 'status']),
        ]
    
    def __str__(self):
        return f"Trade offer from {self.sender.username} to {self.recipient.username}"
    
    def clean(self):
        """Validate the trade offer."""
        from django.core.exceptions import ValidationError
        
        # Don't allow trading with yourself
        if self.sender == self.recipient:
            raise ValidationError("You cannot trade with yourself.")
        
        # Validate that sender owns the offered Pokémon
        for pokemon in self.offered_pokemon.all():
            if pokemon.user != self.sender:
                raise ValidationError(f"You don't own {pokemon.card.name}.")
        
        # Validate that recipient owns the requested Pokémon
        for pokemon in self.requested_pokemon.all():
            if pokemon.user != self.recipient:
                raise ValidationError(f"{self.recipient.username} doesn't own {pokemon.card.name}.")
        
        # Don't allow trading the same Pokémon
        if self.offered_pokemon.filter(id__in=self.requested_pokemon.values_list('id', flat=True)).exists():
            raise ValidationError("Cannot trade the same Pokémon in both directions.")

class TradeHistory(models.Model):
    """Records completed trades for history and analytics."""
    
    trade_offer = models.OneToOneField(
        TradeOffer,
        on_delete=models.CASCADE,
        related_name='history',
        help_text="The original trade offer"
    )
    
    completed_at = models.DateTimeField(
        default=timezone.now,
        help_text="When the trade was completed"
    )
    
    status = models.CharField(
        max_length=20,
        choices=TradeOffer.STATUS_CHOICES,
        default='completed',
        help_text="Final status of the trade"
    )
    
    class Meta:
        ordering = ['-completed_at']
        verbose_name_plural = "Trade histories"
    
    def __str__(self):
        return f"Trade history for {self.trade_offer}"

class TradeNotification(models.Model):
    """Tracks trade-related notifications for users."""
    
    NOTIFICATION_TYPES = [
        ('offer_received', 'New Trade Offer'),
        ('offer_accepted', 'Trade Accepted'),
        ('offer_declined', 'Trade Declined'),
        ('trade_completed', 'Trade Completed'),
        ('trade_cancelled', 'Trade Cancelled'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='trade_notifications',
        help_text="User who should receive the notification"
    )
    
    trade_offer = models.ForeignKey(
        TradeOffer,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="Related trade offer",
        null=True,
        blank=True
    )
    
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        help_text="Type of notification",
        default='offer_received'
    )
    
    is_read = models.BooleanField(
        default=False,
        help_text="Whether the user has read this notification"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.get_notification_type_display()} for {self.user.username}"
