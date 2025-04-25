from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Q

# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    join_date = models.DateTimeField(auto_now_add=True)
    coins = models.IntegerField(default=1000)  # Initial coins for new users
    
    @property
    def pokemon_count(self):
        """Return the number of Pokémon cards owned by the user."""
        return self.user.pokemon.count()
    
    @property
    def trade_count(self):
        """Return the number of completed trades by the user."""
        from trading.models import TradeOffer
        return TradeOffer.objects.filter(
            Q(sender=self.user) | Q(recipient=self.user),
            status__in=['accepted', 'completed']
        ).count()
    
    @property
    def market_listings(self):
        """Return the number of active market listings by the user."""
        from marketplace.models import MarketplaceListing
        return MarketplaceListing.objects.filter(
            seller=self.user,
            status='active'
        ).count()
    
    def __str__(self):
        return self.user.username

class NotificationPreferences(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    trading_notifications = models.BooleanField(default=True)
    marketplace_notifications = models.BooleanField(default=True)

    def __str__(self):
        return f"Notification preferences for {self.user.username}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

@receiver(post_save, sender=User)
def create_notification_preferences(sender, instance, created, **kwargs):
    """Create notification preferences when a new user is created."""
    if created:
        NotificationPreferences.objects.create(user=instance)
