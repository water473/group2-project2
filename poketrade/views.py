from django.shortcuts import render
from pokemon.models import UserPokemon

def home(request):
    # Get featured Pokémon (currently for sale, ordered by rarity and most recently listed)
    featured_pokemon = UserPokemon.objects.filter(is_for_sale=True).order_by('-card__rarity', '-acquired_date')[:4]
    
    return render(request, 'home.html', {
        'featured_pokemon': featured_pokemon
    })

def about(request):
    return render(request, 'about.html') 