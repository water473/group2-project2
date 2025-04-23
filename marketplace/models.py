from django.db import models
from django.contrib.auth.models import User
from pokemon.models import Pokemon, UserCollection, UserPokemon
from django.utils import timezone

class MarketplaceListing(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('sold', 'Sold'),
        ('cancelled', 'Cancelled')
    ]

    pokemon = models.ForeignKey(UserPokemon, on_delete=models.CASCADE, related_name='marketplace_listings')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='marketplace_listings')
    price = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sold_at = models.DateTimeField(null=True, blank=True)
    buyer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='marketplace_purchases')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['price']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.pokemon.pokemon.name} - {self.price} coins"

    def save(self, *args, **kwargs):
        if self.status == 'sold' and not self.sold_at:
            self.sold_at = timezone.now()
        super().save(*args, **kwargs)

    def complete_sale(self, buyer):
        if self.status != 'active':
            return False
        
        # Transfer Pokemon ownership
        self.pokemon.user = buyer
        self.pokemon.save()
        
        # Update listing status
        self.status = 'sold'
        self.buyer = buyer
        self.save()
        
        # Transfer coins
        self.seller.profile.coins += self.price
        self.seller.profile.save()
        buyer.profile.coins -= self.price
        buyer.profile.save()
        
        return True

class Transaction(models.Model):
    # Transaction details
    listing = models.ForeignKey(MarketplaceListing, on_delete=models.CASCADE, related_name='transactions')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transaction_purchases')
    price_paid = models.IntegerField()
    
    # Transaction timestamp
    transaction_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.buyer.username} purchased {self.listing.pokemon.pokemon.name} from {self.listing.seller.username}"
    
    class Meta:
        ordering = ['-transaction_date']

class MarketplaceNotification(models.Model):
    NOTIFICATION_TYPES = [
        ('listing_sold', 'Listing Sold'),
        ('purchase_successful', 'Purchase Successful'),
        ('listing_cancelled', 'Listing Cancelled')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='marketplace_notifications')
    listing = models.ForeignKey(MarketplaceListing, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.listing.pokemon.pokemon.name}"

class SavedListing(models.Model):
    # User who saved the listing
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_listings')
    listing = models.ForeignKey(MarketplaceListing, on_delete=models.CASCADE, related_name='saved_by')
    
    # When the listing was saved
    saved_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} saved {self.listing.pokemon.pokemon.name}"
    
    class Meta:
        # Each user can save a listing only once
        unique_together = ['user', 'listing']
        ordering = ['-saved_at']
