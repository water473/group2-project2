from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'trading'

urlpatterns = [
    # Redirect root trading URL to offers
    path('', RedirectView.as_view(pattern_name='trading:trade_offers'), name='home'),
    
    # API endpoints
    path('api/users/<int:user_id>/pokemon/', views.get_user_pokemon, name='api_user_pokemon'),
    
    # Trade offers
    path('offers/', views.trade_offers, name='trade_offers'),
    path('offers/new/', views.create_trade_offer, name='create_trade_offer'),
    path('offers/<int:offer_id>/', views.trade_offer_detail, name='trade_offer_detail'),
    path('offers/<int:offer_id>/accept/', views.accept_trade_offer, name='accept_trade_offer'),
    path('offers/<int:offer_id>/decline/', views.decline_trade_offer, name='decline_trade_offer'),
    path('offers/<int:offer_id>/cancel/', views.cancel_trade_offer, name='cancel_trade_offer'),
    
    # Trade history
    path('history/', views.trade_history, name='trade_history'),
    path('history/<int:trade_id>/', views.trade_history_detail, name='trade_history_detail'),
    
    # Notifications
    path('notifications/', views.trade_notifications, name='trade_notifications'),
    path('notifications/mark-read/', views.mark_notifications_read, name='mark_notifications_read'),
] 