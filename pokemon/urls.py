from django.urls import path
from . import views

app_name = 'pokemon'

urlpatterns = [
    path('collection/', views.collection, name='collection'),
    path('collection/sort/<str:sort_by>/', views.collection, name='collection_sorted'),
    path('collection/filter/<str:filter_by>/<str:filter_value>/', views.collection, name='collection_filtered'),
    path('pokemon/<int:pokemon_id>/', views.pokemon_detail, name='pokemon_detail'),
    path('collection/pokemon/<int:collection_id>/', views.collection_pokemon_detail, name='collection_pokemon_detail'),
    path('collection/pokemon/<int:collection_id>/edit/', views.edit_collection_pokemon, name='edit_collection_pokemon'),
    path('collection/<int:pokemon_id>/edit/', views.edit_collection_pokemon, name='edit_collection_pokemon'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/add/<int:card_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:card_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('cards/', views.card_list, name='card_list'),
] 