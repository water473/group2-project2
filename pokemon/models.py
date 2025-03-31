from django.db import models
from django.contrib.auth.models import User

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
