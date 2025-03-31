from django.db import models
from django.contrib.auth.models import User
from pokemon.models import Pokemon, UserCollection

class MarketplaceListing(models.Model):
    # Seller and Pokemon information
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='marketplace_listings')
    pokemon = models.ForeignKey(UserCollection, on_delete=models.CASCADE, related_name='marketplace_listings')
    
    # Listing details
    price = models.IntegerField()
    description = models.TextField(blank=True)
    
    # Listing status
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('sold', 'Sold'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.pokemon.pokemon.name} - {self.price} coins by {self.seller.username}"
    
    class Meta:
        ordering = ['-created_at']

class Transaction(models.Model):
    # Transaction details
    listing = models.ForeignKey(MarketplaceListing, on_delete=models.CASCADE, related_name='transactions')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    price_paid = models.IntegerField()
    
    # Transaction timestamp
    transaction_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.buyer.username} purchased {self.listing.pokemon.pokemon.name} from {self.listing.seller.username}"
    
    class Meta:
        ordering = ['-transaction_date']

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
