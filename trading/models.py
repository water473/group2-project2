from django.db import models
from django.contrib.auth.models import User
from pokemon.models import Pokemon, UserCollection

class TradeOffer(models.Model):
    # Trade participants
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_trades')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_trades')
    
    # Trade status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Optional message with the trade
    message = models.TextField(blank=True)
    
    def __str__(self):
        return f"Trade #{self.id}: {self.sender.username} to {self.receiver.username} ({self.status})"
    
    class Meta:
        ordering = ['-created_at']

class TradeItem(models.Model):
    trade = models.ForeignKey(TradeOffer, on_delete=models.CASCADE, related_name='items')
    
    # The Pokemon being offered in the trade
    pokemon_offered = models.ForeignKey(UserCollection, on_delete=models.CASCADE, related_name='trade_offers')
    
    # Whether this is from the sender or receiver
    is_sender_item = models.BooleanField(default=True)
    
    def __str__(self):
        direction = "→" if self.is_sender_item else "←"
        return f"{self.pokemon_offered.pokemon.name} {direction}"

class TradeNotification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trade_notifications')
    trade = models.ForeignKey(TradeOffer, on_delete=models.CASCADE)
    
    # Notification content
    message = models.CharField(max_length=255)
    
    # Read status
    is_read = models.BooleanField(default=False)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Notification for {self.user.username} about Trade #{self.trade.id}"
    
    class Meta:
        ordering = ['-created_at']
