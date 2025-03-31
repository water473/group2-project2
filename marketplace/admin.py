from django.contrib import admin
from .models import MarketplaceListing, Transaction, SavedListing

@admin.register(MarketplaceListing)
class MarketplaceListingAdmin(admin.ModelAdmin):
    list_display = ('id', 'seller', 'pokemon', 'price', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('seller__username', 'pokemon__pokemon__name', 'description')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('listing', 'buyer', 'price_paid', 'transaction_date')
    list_filter = ('transaction_date',)
    search_fields = ('buyer__username', 'listing__pokemon__pokemon__name')

@admin.register(SavedListing)
class SavedListingAdmin(admin.ModelAdmin):
    list_display = ('user', 'listing', 'saved_at')
    list_filter = ('saved_at',)
    search_fields = ('user__username', 'listing__pokemon__pokemon__name')
