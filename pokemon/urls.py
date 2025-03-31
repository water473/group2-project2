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
] 