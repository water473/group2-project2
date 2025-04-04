from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PokemonCard, UserPokemon

# Create your views here.

@login_required
def collection(request, sort_by=None, filter_by=None, filter_value=None):
    """View the user's Pokemon collection."""
    # Get the user's collection
    collection = UserPokemon.objects.filter(user=request.user)
    
    # Apply filters if provided
    if filter_by and filter_value:
        if filter_by == 'type':
            # Filter by types stored in JSON field
            collection = collection.filter(card__types__contains=[filter_value])
        elif filter_by == 'rarity':
            collection = collection.filter(card__rarity=filter_value)
    
    # Apply sorting if provided
    if sort_by:
        if sort_by == 'name':
            collection = collection.order_by('card__name')
        elif sort_by == 'date':
            collection = collection.order_by('-acquired_date')
        elif sort_by == 'rarity':
            collection = collection.order_by('card__rarity')
    
    # Get all Pokemon types and rarities for the filter dropdowns
    # We'll need to extract these from the cards in the database
    all_cards = PokemonCard.objects.all()
    pokemon_types = set()
    pokemon_rarities = set()
    
    for card in all_cards:
        if card.types:
            pokemon_types.update(card.types)
        if card.rarity:
            pokemon_rarities.add(card.rarity)
    
    context = {
        'collection': collection,
        'pokemon_types': sorted(list(pokemon_types)),
        'pokemon_rarities': sorted(list(pokemon_rarities)),
        'current_sort': sort_by,
        'current_filter_by': filter_by,
        'current_filter_value': filter_value,
    }
    
    return render(request, 'pokemon/collection.html', context)

@login_required
def pokemon_detail(request, card_id):
    """View details of a specific Pokemon card."""
    card = get_object_or_404(PokemonCard, card_id=card_id)
    return render(request, 'pokemon/pokemon_detail.html', {'card': card})

@login_required
def collection_pokemon_detail(request, collection_id):
    """View details of a specific Pokemon from the user's collection."""
    user_pokemon = get_object_or_404(UserPokemon, id=collection_id, user=request.user)
    return render(request, 'pokemon/collection_pokemon_detail.html', {'user_pokemon': user_pokemon})

@login_required
def edit_collection_pokemon(request, collection_id):
    """Edit a Pokemon in the user's collection (e.g., add nickname, mark as favorite)."""
    user_pokemon = get_object_or_404(UserPokemon, id=collection_id, user=request.user)
    
    if request.method == 'POST':
        # Update the user's Pokemon
        user_pokemon.nickname = request.POST.get('nickname', '')
        user_pokemon.description = request.POST.get('description', '')
        user_pokemon.is_for_sale = 'is_for_sale' in request.POST
        if user_pokemon.is_for_sale:
            user_pokemon.price = request.POST.get('price', user_pokemon.card.base_value)
        user_pokemon.save()
        
        messages.success(request, f'Pokemon "{user_pokemon.card.name}" updated successfully!')
        return redirect('pokemon:collection_pokemon_detail', collection_id=user_pokemon.id)
    
    return render(request, 'pokemon/edit_collection_pokemon.html', {'user_pokemon': user_pokemon})
