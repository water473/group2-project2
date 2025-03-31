from django.urls import path
from . import views

app_name = 'trading'

urlpatterns = [
    path('', views.trade_home, name='home'),
    path('create/<str:username>/', views.create_trade, name='create_trade'),
    path('create/<str:username>/<int:pokemon_id>/', views.create_trade_with_pokemon, name='create_trade_with_pokemon'),
    path('sent/', views.sent_trades, name='sent_trades'),
    path('received/', views.received_trades, name='received_trades'),
    path('view/<int:trade_id>/', views.view_trade, name='view_trade'),
    path('accept/<int:trade_id>/', views.accept_trade, name='accept_trade'),
    path('reject/<int:trade_id>/', views.reject_trade, name='reject_trade'),
    path('cancel/<int:trade_id>/', views.cancel_trade, name='cancel_trade'),
    path('notifications/', views.trade_notifications, name='notifications'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
] 