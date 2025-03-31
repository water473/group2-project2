from django.urls import path
from . import views

app_name = 'marketplace'

urlpatterns = [
    path('', views.marketplace_home, name='home'),
    path('create/<int:pokemon_id>/', views.create_listing, name='create_listing'),
    path('listing/<int:listing_id>/', views.view_listing, name='view_listing'),
    path('listing/<int:listing_id>/edit/', views.edit_listing, name='edit_listing'),
    path('listing/<int:listing_id>/cancel/', views.cancel_listing, name='cancel_listing'),
    path('listing/<int:listing_id>/purchase/', views.purchase, name='purchase'),
    path('my-listings/', views.my_listings, name='my_listings'),
    path('purchases/', views.purchase_history, name='purchase_history'),
    path('saved/', views.saved_listings, name='saved_listings'),
    path('listing/<int:listing_id>/save/', views.save_listing, name='save_listing'),
    path('listing/<int:listing_id>/unsave/', views.unsave_listing, name='unsave_listing'),
    path('search/', views.search_marketplace, name='search'),
] 