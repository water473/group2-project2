from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Pokemon, UserCollection

# Create your views here.

@login_required
def collection(request, sort_by=None, filter_by=None, filter_value=None):
    """View the user's Pokemon collection."""
    # Get the user's collection
    collection = UserCollection.objects.filter(user=request.user)
    
    # Apply filters if provided
    if filter_by and filter_value:
        if filter_by == 'type':
            collection = collection.filter(pokemon__primary_type=filter_value) | collection.filter(pokemon__secondary_type=filter_value)
        elif filter_by == 'rarity':
            collection = collection.filter(pokemon__rarity=filter_value)
    
    # Apply sorting if provided
    if sort_by:
        if sort_by == 'name':
            collection = collection.order_by('pokemon__name')
        elif sort_by == 'date':
            collection = collection.order_by('-acquired_date')
        elif sort_by == 'rarity':
            collection = collection.order_by('-pokemon__rarity')
    
    # Get all Pokemon types and rarities for the filter dropdowns
    pokemon_types = Pokemon.type_choices
    pokemon_rarities = Pokemon.rarity_choices
    
    context = {
        'collection': collection,
        'pokemon_types': pokemon_types,
        'pokemon_rarities': pokemon_rarities,
        'current_sort': sort_by,
        'current_filter_by': filter_by,
        'current_filter_value': filter_value,
    }
    
    return render(request, 'pokemon/collection.html', context)

@login_required
def pokemon_detail(request, pokemon_id):
    """View details of a specific Pokemon."""
    pokemon = get_object_or_404(Pokemon, id=pokemon_id)
    return render(request, 'pokemon/pokemon_detail.html', {'pokemon': pokemon})

@login_required
def collection_pokemon_detail(request, collection_id):
    """View details of a specific Pokemon from the user's collection."""
    user_pokemon = get_object_or_404(UserCollection, id=collection_id, user=request.user)
    return render(request, 'pokemon/collection_pokemon_detail.html', {'user_pokemon': user_pokemon})

@login_required
def edit_collection_pokemon(request, collection_id):
    """Edit a Pokemon in the user's collection (e.g., add nickname, mark as favorite)."""
    user_pokemon = get_object_or_404(UserCollection, id=collection_id, user=request.user)
    
    if request.method == 'POST':
        # Update the user's Pokemon
        user_pokemon.nickname = request.POST.get('nickname', '')
        user_pokemon.favorite = 'favorite' in request.POST
        user_pokemon.save()
        
        messages.success(request, f'Pokemon "{user_pokemon.pokemon.name}" updated successfully!')
        return redirect('pokemon:collection_pokemon_detail', collection_id=user_pokemon.id)
    
    return render(request, 'pokemon/edit_collection_pokemon.html', {'user_pokemon': user_pokemon})
