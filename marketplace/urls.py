from django.urls import path
from . import views

app_name = 'marketplace'

urlpatterns = [
    path('', views.marketplace, name='marketplace'),
    path('create/<int:collection_id>/', views.create_listing, name='create_listing'),
    path('listing/<int:listing_id>/', views.view_listing, name='view_listing'),
    path('listing/<int:listing_id>/edit/', views.edit_listing, name='edit_listing'),
    path('listing/<int:listing_id>/cancel/', views.cancel_listing, name='cancel_listing'),
    path('listing/<int:listing_id>/purchase/', views.purchase_pokemon, name='purchase'),
    path('my-listings/', views.my_listings, name='my_listings'),
    path('purchase-history/', views.purchase_history, name='purchase_history'),
    path('saved-listings/', views.saved_listings, name='saved_listings'),
    path('listing/<int:listing_id>/save/', views.save_listing, name='save_listing'),
    path('listing/<int:listing_id>/unsave/', views.unsave_listing, name='unsave_listing'),
    path('search/', views.search_marketplace, name='search'),
] 