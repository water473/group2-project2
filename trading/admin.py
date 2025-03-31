from django.contrib import admin
from .models import TradeOffer, TradeItem, TradeNotification

@admin.register(TradeOffer)
class TradeOfferAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'receiver', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('sender__username', 'receiver__username', 'message')

@admin.register(TradeItem)
class TradeItemAdmin(admin.ModelAdmin):
    list_display = ('trade', 'pokemon_offered', 'is_sender_item')
    list_filter = ('is_sender_item',)
    search_fields = ('trade__id', 'pokemon_offered__pokemon__name')

@admin.register(TradeNotification)
class TradeNotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'trade', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'message')
