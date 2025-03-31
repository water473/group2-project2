from django.contrib import admin
from .models import Pokemon, UserCollection

@admin.register(Pokemon)
class PokemonAdmin(admin.ModelAdmin):
    list_display = ('name', 'pokemon_id', 'primary_type', 'secondary_type', 'rarity', 'base_value')
    list_filter = ('primary_type', 'secondary_type', 'rarity')
    search_fields = ('name', 'description')

@admin.register(UserCollection)
class UserCollectionAdmin(admin.ModelAdmin):
    list_display = ('user', 'pokemon', 'acquired_date', 'nickname', 'favorite')
    list_filter = ('acquired_date', 'favorite')
    search_fields = ('user__username', 'pokemon__name', 'nickname')
