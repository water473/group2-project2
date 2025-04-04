from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Pokemon(models.Model):
    # Basic Pokemon information
    name = models.CharField(max_length=100)
    pokemon_id = models.IntegerField(unique=True)  # The ID from the Pokemon API
    image_url = models.URLField()
    
    # Pokemon attributes
    type_choices = [
        ('normal', 'Normal'),
        ('fire', 'Fire'),
        ('water', 'Water'),
        ('grass', 'Grass'),
        ('electric', 'Electric'),
        ('ice', 'Ice'),
        ('fighting', 'Fighting'),
        ('poison', 'Poison'),
        ('ground', 'Ground'),
        ('flying', 'Flying'),
        ('psychic', 'Psychic'),
        ('bug', 'Bug'),
        ('rock', 'Rock'),
        ('ghost', 'Ghost'),
        ('dragon', 'Dragon'),
        ('dark', 'Dark'),
        ('steel', 'Steel'),
        ('fairy', 'Fairy'),
    ]
    primary_type = models.CharField(max_length=20, choices=type_choices)
    secondary_type = models.CharField(max_length=20, choices=type_choices, blank=True, null=True)
    
    # Rarity will affect card value
    rarity_choices = [
        ('common', 'Common'),
        ('uncommon', 'Uncommon'),
        ('rare', 'Rare'),
        ('ultra_rare', 'Ultra Rare'),
        ('legendary', 'Legendary'),
    ]
    rarity = models.CharField(max_length=20, choices=rarity_choices)
    
    # Base value (can be used for marketplace pricing)
    base_value = models.IntegerField(default=100)
    
    # Additional details
    description = models.TextField(blank=True)
    height = models.FloatField(default=0)
    weight = models.FloatField(default=0)
    
    def __str__(self):
        return f"{self.name} ({self.primary_type})"
    
    class Meta:
        ordering = ['name']

class UserCollection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collection')
    pokemon = models.ForeignKey(Pokemon, on_delete=models.CASCADE)
    acquired_date = models.DateTimeField(auto_now_add=True)
    
    # Custom attributes for the user's specific Pokemon
    nickname = models.CharField(max_length=100, blank=True)
    favorite = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username}'s {self.pokemon.name}"
    
    class Meta:
        # Each user can have only one of each Pokemon in their collection
        # (This can be removed if users can have multiple of the same Pokemon)
        unique_together = ['user', 'pokemon']
        ordering = ['-acquired_date']

class PokemonCard(models.Model):
    """Model for storing Pokémon card data from the TCG API"""
    card_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    set_name = models.CharField(max_length=100)
    set_code = models.CharField(max_length=20)
    rarity = models.CharField(max_length=50, blank=True)
    image_url = models.URLField()
    small_image_url = models.URLField(blank=True)
    large_image_url = models.URLField(blank=True)
    card_market_url = models.URLField(blank=True)
    tcgplayer_url = models.URLField(blank=True)
    cardmarket_url = models.URLField(blank=True)
    cardmarket_prices = models.JSONField(null=True, blank=True)
    tcgplayer_prices = models.JSONField(null=True, blank=True)
    types = models.JSONField(null=True, blank=True)  # Store as JSON array
    weaknesses = models.JSONField(null=True, blank=True)  # Store as JSON array
    resistances = models.JSONField(null=True, blank=True)  # Store as JSON array
    retreat_cost = models.JSONField(null=True, blank=True)  # Store as JSON array
    converted_retreat_cost = models.IntegerField(null=True, blank=True)
    hp = models.CharField(max_length=10, blank=True)
    artist = models.CharField(max_length=100, blank=True)
    flavor_text = models.TextField(blank=True)
    national_pokedex_numbers = models.JSONField(null=True, blank=True)  # Store as JSON array
    legalities = models.JSONField(null=True, blank=True)  # Store as JSON object
    regulation_mark = models.CharField(max_length=10, blank=True)
    base_value = models.IntegerField(default=10)  # Default value for trading
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.set_name})"

    class Meta:
        ordering = ['name', 'set_name']

class UserPokemon(models.Model):
    """Model for storing user's Pokémon card collection"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pokemon')
    card = models.ForeignKey(PokemonCard, on_delete=models.CASCADE)
    nickname = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    is_for_sale = models.BooleanField(default=False)
    price = models.IntegerField(null=True, blank=True)
    acquired_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s {self.card.name}"

    class Meta:
        ordering = ['-acquired_date']
        unique_together = ['user', 'card']  # Prevent duplicates in collection
