from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PokemonCard, UserPokemon, WishlistItem
from marketplace.models import MarketplaceListing
from django.http import JsonResponse
from django.urls import reverse

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
            user_pokemon = user_pokemon.filter(card__types__name=filter_value)
        elif filter_type == 'rarity':
            user_pokemon = user_pokemon.filter(card__rarity=filter_value)
    
    # Apply sorting
    if sort == 'name':
        user_pokemon = user_pokemon.order_by('card__name')
    elif sort == 'date':
        user_pokemon = user_pokemon.order_by('-acquired_date')
    elif sort == 'rarity':
        user_pokemon = user_pokemon.order_by('card__rarity')
    
    # Get all Pokemon types and rarities for the filter dropdowns
    pokemon_types = set(PokemonCard.objects.values_list('types__name', flat=True).distinct())
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
