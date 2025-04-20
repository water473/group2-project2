from django.contrib import admin
from .models import TradeOffer, TradeHistory, TradeNotification

@admin.register(TradeOffer)
class TradeOfferAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'recipient', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('sender__username', 'recipient__username', 'message')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('offered_pokemon', 'requested_pokemon')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sender', 'recipient')

@admin.register(TradeHistory)
class TradeHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'trade_offer', 'status', 'completed_at')
    list_filter = ('status', 'completed_at')
    search_fields = ('trade_offer__sender__username', 'trade_offer__recipient__username')
    readonly_fields = ('completed_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('trade_offer__sender', 'trade_offer__recipient')

@admin.register(TradeNotification)
class TradeNotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'trade_offer__sender__username', 'trade_offer__recipient__username')
    readonly_fields = ('created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'trade_offer__sender', 'trade_offer__recipient')
