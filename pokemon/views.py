from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PokemonCard, UserPokemon, WishlistItem
from marketplace.models import MarketplaceListing
from django.http import JsonResponse
from django.urls import reverse
import logging

# Create your views here.

@login_required
def collection(request):
    """View the user's Pokemon collection."""
    # Get filter and sort parameters
    filter_type = request.GET.get('filter_type')
    filter_value = request.GET.get('filter_value')
    sort = request.GET.get('sort', 'name')  # Default sort by name
    
    # Get the user's collection
    user_pokemon = UserPokemon.objects.filter(user=request.user)
    
    # Apply filters if provided
    if filter_type and filter_value:
        if filter_type == 'type':
            # Filter by type using a list comprehension
            user_pokemon = [pokemon for pokemon in user_pokemon 
                          if filter_value in pokemon.card.types]
        elif filter_type == 'rarity':
            user_pokemon = user_pokemon.filter(card__rarity=filter_value)
    
    # Apply sorting
    if sort == 'name':
        user_pokemon = sorted(user_pokemon, key=lambda x: x.card.name)
    elif sort == 'date':
        user_pokemon = sorted(user_pokemon, key=lambda x: x.acquired_date, reverse=True)
    elif sort == 'rarity':
        user_pokemon = sorted(user_pokemon, key=lambda x: x.card.rarity)
    
    # Get all Pokemon types and rarities for the filter dropdowns
    pokemon_types = set()
    for card in PokemonCard.objects.all():
        if card.types:
            pokemon_types.update(card.types)
    pokemon_rarities = set(PokemonCard.objects.values_list('rarity', flat=True).distinct())
    
    context = {
        'user_pokemon': user_pokemon,
        'pokemon_types': sorted(list(pokemon_types)),
        'pokemon_rarities': sorted(list(pokemon_rarities)),
        'filter_type': filter_type,
        'filter_value': filter_value,
        'sort': sort,
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
        # Get the previous state of is_for_sale
        was_for_sale = user_pokemon.is_for_sale
        
        # Update the user's Pokemon
        user_pokemon.nickname = request.POST.get('nickname', '')
        user_pokemon.description = request.POST.get('description', '')
        user_pokemon.is_for_sale = 'is_for_sale' in request.POST
        
        # Handle marketplace listing
        if user_pokemon.is_for_sale:
            price = int(request.POST.get('price', user_pokemon.card.base_value))
            user_pokemon.price = price
            
            # Create marketplace listing if it doesn't exist
            if not was_for_sale:
                MarketplaceListing.objects.create(
                    pokemon=user_pokemon,
                    seller=request.user,
                    price=price,
                    status='active'
                )
                messages.success(request, f'{user_pokemon.card.name} has been listed in the marketplace for {price} coins!')
        else:
            # If Pokemon was previously for sale but now isn't, cancel any active listings
            if was_for_sale:
                active_listing = MarketplaceListing.objects.filter(
                    pokemon=user_pokemon,
                    status='active'
                ).first()
                if active_listing:
                    active_listing.status = 'cancelled'
                    active_listing.save()
                    messages.info(request, f'{user_pokemon.card.name} has been removed from the marketplace.')
        
        user_pokemon.save()
        messages.success(request, f'Pokemon "{user_pokemon.card.name}" updated successfully!')
        return redirect('pokemon:collection_pokemon_detail', collection_id=user_pokemon.id)
    
    return render(request, 'pokemon/edit_collection_pokemon.html', {'user_pokemon': user_pokemon})

@login_required
def wishlist(request):
    wishlist_items = WishlistItem.objects.filter(user=request.user).select_related('pokemon_card')
    return render(request, 'pokemon/wishlist.html', {'wishlist_items': wishlist_items})

@login_required
def add_to_wishlist(request, card_id):
    card = get_object_or_404(PokemonCard, id=card_id)
    
    if not WishlistItem.objects.filter(user=request.user, pokemon_card=card).exists():
        WishlistItem.objects.create(user=request.user, pokemon_card=card)
        messages.success(request, f"{card.name} added to your wishlist!")
    else:
        messages.info(request, f"{card.name} is already in your wishlist!")
    
    return redirect('pokemon:card_list')

@login_required
def remove_from_wishlist(request, card_id):
    """Remove a card from the user's wishlist."""
    if request.method == 'POST':
        try:
            wishlist_item = WishlistItem.objects.get(
                user=request.user,
                pokemon_card_id=card_id
            )
            wishlist_item.delete()
            messages.success(request, 'Card removed from wishlist.')
        except WishlistItem.DoesNotExist:
            messages.error(request, 'Card not found in wishlist.')
    
    # Get the next URL from POST data, fallback to wishlist page
    next_url = request.POST.get('next', reverse('pokemon:wishlist'))
    return redirect(next_url)

@login_required
def card_list(request):
    """View all available Pokemon cards."""
    # Get filter parameters
    search_query = request.GET.get('search', '')
    type_filter = request.GET.get('type', '')
    rarity_filter = request.GET.get('rarity', '')
    
    # Start with all cards
    cards = PokemonCard.objects.all()
    
    # Apply filters
    if search_query:
        cards = cards.filter(name__icontains=search_query)
    
    if type_filter:
        cards = cards.filter(types__icontains=type_filter)
    
    if rarity_filter:
        cards = cards.filter(rarity=rarity_filter)
    
    # Get all available types and rarities for filters
    types = set()
    rarities = set()
    for card in PokemonCard.objects.all():
        if card.types:
            types.update(card.types)
        if card.rarity:
            rarities.add(card.rarity)
    
    # Get user's wishlist items
    wishlist_cards = set(WishlistItem.objects.filter(
        user=request.user
    ).values_list('pokemon_card_id', flat=True))
    
    context = {
        'cards': cards,
        'types': sorted(list(types)),
        'rarities': sorted(list(rarities)),
        'search_query': search_query,
        'type_filter': type_filter,
        'rarity_filter': rarity_filter,
        'wishlist_cards': wishlist_cards,
    }
    
    return render(request, 'pokemon/card_list.html', context)

@login_required
def generate_description(request):
    """Generate a description for a Pokemon using OpenRouter API."""
    if request.method == 'POST':
        import json
        import os
        import requests
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            data = json.loads(request.body)
            pokemon_name = data.get('pokemon_name')
            logger.info(f"Generating description for Pokemon: {pokemon_name}")
            
            if not pokemon_name:
                return JsonResponse({'error': 'Pokemon name is required'}, status=400)
            
            api_key = os.getenv("OPEN_ROUTER_API_KEY")
            if not api_key:
                logger.error("OPEN_ROUTER_API_KEY not found in environment variables")
                return JsonResponse({'error': 'API key not found'}, status=500)
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
                'HTTP-Referer': request.build_absolute_uri('/'),
                'X-Title': 'PokeTrade'
            }
            
            logger.info("Making API request to OpenRouter")
            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers=headers,
                json={
                    'model': 'deepseek/deepseek-r1:free',
                    'messages': [{
                        'role': 'user',
                        'content': f'Write a brief, engaging description for the Pokemon {pokemon_name}. Keep it under 50 words. Do not include the work count or any other text other than the description.'
                    }]
                }
            )
            
            logger.info(f"OpenRouter API response status: {response.status_code}")
            logger.info(f"OpenRouter API response: {response.text}")
            
            if response.status_code == 200:
                description = response.json()['choices'][0]['message']['content']
                return JsonResponse({'description': description})
            else:
                error_msg = f'API Error: {response.status_code} - {response.text}'
                logger.error(error_msg)
                return JsonResponse({'error': error_msg}, status=500)
                
        except Exception as e:
            logger.exception("Exception in generate_description view")
            return JsonResponse({'error': f'Exception: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
