from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import MarketplaceListing, Transaction, SavedListing, MarketplaceNotification
from pokemon.models import UserCollection, Pokemon, UserPokemon, PokemonCard
from .forms import ListingForm
from django.utils import timezone
from messaging.models import Message
from messaging.models import Conversation

@login_required
def marketplace_home(request):
    """Marketplace homepage with active listings."""
    # Get all active listings except the user's own
    listings = MarketplaceListing.objects.filter(
        status='active'
    ).exclude(
        seller=request.user
    ).order_by('-created_at')
    
    # Get Pokemon types and rarities for filters
    pokemon_types = Pokemon.type_choices
    pokemon_rarities = Pokemon.rarity_choices
    
    context = {
        'listings': listings,
        'pokemon_types': pokemon_types,
        'pokemon_rarities': pokemon_rarities,
    }
    
    return render(request, 'marketplace/home.html', context)

@login_required
def marketplace(request):
    # Get all active listings except the user's own
    listings = MarketplaceListing.objects.filter(
        status='active'
    ).select_related(
        'pokemon',
        'pokemon__card',
        'seller',
        'seller__profile'
    ).order_by('-created_at')
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    pokemon_type = request.GET.get('type', '')
    rarity = request.GET.get('rarity', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    
    # Apply filters
    if search_query:
        listings = listings.filter(
            Q(pokemon__card__name__icontains=search_query) |
            Q(pokemon__nickname__icontains=search_query)
        )
    
    if pokemon_type:
        # Convert to lowercase for case-insensitive matching
        pokemon_type = pokemon_type.lower()
        listings = listings.extra(
            where=["LOWER(pokemon_pokemoncard.types) LIKE %s"],
            params=[f'%{pokemon_type}%']
        )
    
    if rarity:
        listings = listings.filter(pokemon__card__rarity__iexact=rarity)
    
    if min_price:
        try:
            min_price = int(min_price)
            listings = listings.filter(price__gte=min_price)
        except ValueError:
            pass
    
    if max_price:
        try:
            max_price = int(max_price)
            listings = listings.filter(price__lte=max_price)
        except ValueError:
            pass
    
    context = {
        'listings': listings,
        'search_query': search_query,
        'pokemon_type': pokemon_type,
        'selected_rarity': rarity,
        'min_price': min_price,
        'max_price': max_price,
        'pokemon_types': [type[0] for type in Pokemon.type_choices],
        'rarities': PokemonCard.objects.values_list('rarity', flat=True).distinct().order_by('rarity'),
    }
    return render(request, 'marketplace/marketplace.html', context)

@login_required
def create_listing(request, collection_id):
    # Get the Pokemon from user's collection
    pokemon = get_object_or_404(UserPokemon, id=collection_id, user=request.user)
    
    # Check if Pokemon is already listed
    if MarketplaceListing.objects.filter(pokemon=pokemon, status='active').exists():
        messages.error(request, "This Pokemon is already listed in the marketplace!")
        return redirect('pokemon:collection')
    
    if request.method == 'POST':
        form = ListingForm(request.POST)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.pokemon = pokemon
            listing.seller = request.user
            listing.status = 'active'
            listing.save()
            
            # Update Pokemon's status
            pokemon.is_for_sale = True
            pokemon.save()
            
            messages.success(request, f"{pokemon.card.name} has been listed in the marketplace!")
            return redirect('marketplace:marketplace')
    else:
        # Suggest a price based on Pokemon's base value
        suggested_price = pokemon.card.base_value
        form = ListingForm(initial={'price': suggested_price})
    
    context = {
        'form': form,
        'pokemon': pokemon,
    }
    return render(request, 'marketplace/create_listing.html', context)

@login_required
def view_listing(request, listing_id):
    """View a specific marketplace listing."""
    listing = get_object_or_404(MarketplaceListing, id=listing_id)
    
    # Check if the user has saved this listing
    is_saved = SavedListing.objects.filter(user=request.user, listing=listing).exists()
    
    # Check if the user has enough coins to buy
    can_afford = request.user.profile.coins >= listing.price
    
    context = {
        'listing': listing,
        'is_saved': is_saved,
        'can_afford': can_afford,
        'is_owner': listing.seller == request.user,
    }
    
    return render(request, 'marketplace/view_listing.html', context)

@login_required
def edit_listing(request, listing_id):
    """Edit an existing marketplace listing."""
    listing = get_object_or_404(MarketplaceListing, id=listing_id, seller=request.user, status='active')
    
    if request.method == 'POST':
        price = request.POST.get('price')
        description = request.POST.get('description', '')
        
        # Validate price
        try:
            price = int(price)
            if price <= 0:
                raise ValueError
        except ValueError:
            messages.error(request, "Please enter a valid price!")
            return render(request, 'marketplace/edit_listing.html', {'listing': listing})
        
        # Update listing
        listing.price = price
        listing.description = description
        listing.save()
        
        messages.success(request, "Listing updated successfully!")
        return redirect('marketplace:view_listing', listing_id=listing.id)
    
    return render(request, 'marketplace/edit_listing.html', {'listing': listing})

@login_required
def cancel_listing(request, listing_id):
    listing = get_object_or_404(MarketplaceListing, id=listing_id, seller=request.user)
    
    if listing.status == 'active':
        # Update the listing status
        listing.status = 'cancelled'
        listing.save()
        
        # Reset the Pokemon's listing status
        pokemon = listing.pokemon
        pokemon.is_for_sale = False
        pokemon.price = None  # Reset the price
        pokemon.save()
        
        messages.success(request, f"Listing for {listing.pokemon.card.name} has been cancelled.")
    else:
        messages.error(request, "This listing cannot be cancelled.")
    
    return redirect('marketplace:my_listings')

@login_required
def purchase_pokemon(request, listing_id):
    if request.method != 'POST':
        return redirect('marketplace:marketplace')
        
    # Get the listing and verify it's active
    listing = get_object_or_404(MarketplaceListing, id=listing_id, status='active')
    
    # Prevent buying your own listing
    if listing.seller == request.user:
        messages.error(request, "You cannot purchase your own listing!")
        return redirect('marketplace:marketplace')
    
    # Check if buyer has enough coins
    if request.user.profile.coins < listing.price:
        messages.error(request, "You don't have enough coins for this purchase!")
        return redirect('marketplace:marketplace')
    
    # Process the transaction
    try:
        # Transfer coins
        request.user.profile.coins -= listing.price
        request.user.profile.save()
        
        listing.seller.profile.coins += listing.price
        listing.seller.profile.save()
        
        # Transfer Pokemon ownership
        pokemon = listing.pokemon
        pokemon.user = request.user
        pokemon.is_for_sale = False
        pokemon.save()
        
        # Update listing status
        listing.status = 'sold'
        listing.buyer = request.user
        listing.sold_at = timezone.now()
        listing.save()
        
        # Create transaction record
        transaction = Transaction.objects.create(
            listing=listing,
            buyer=request.user,
            price_paid=listing.price
        )
        
        # Create notifications
        MarketplaceNotification.objects.create(
            user=listing.seller,
            listing=listing,
            notification_type='listing_sold'
        )
        
        MarketplaceNotification.objects.create(
            user=request.user,
            listing=listing,
            notification_type='purchase_successful'
        )
        
        messages.success(request, f"Successfully purchased {pokemon.card.name} for {listing.price} coins!")
        
    except Exception as e:
        messages.error(request, "An error occurred during the purchase. Please try again.")
        return redirect('marketplace:marketplace')
    
    return redirect('pokemon:collection')

@login_required
def my_listings(request):
    """View all listings by the current user."""
    listings = MarketplaceListing.objects.filter(
        seller=request.user
    ).select_related(
        'pokemon',
        'pokemon__card',
        'buyer'
    ).order_by('-created_at')
    
    return render(request, 'marketplace/my_listings.html', {'listings': listings})

@login_required
def purchase_history(request):
    """View the user's purchase history."""
    purchases = Transaction.objects.filter(buyer=request.user).order_by('-transaction_date')
    return render(request, 'marketplace/purchase_history.html', {'purchases': purchases})

@login_required
def saved_listings(request):
    """View the user's saved listings."""
    saved = SavedListing.objects.filter(user=request.user).order_by('-saved_at')
    return render(request, 'marketplace/saved_listings.html', {'saved_listings': saved})

@login_required
def save_listing(request, listing_id):
    """Save a listing to the user's favorites."""
    listing = get_object_or_404(MarketplaceListing, id=listing_id, status='active')
    
    # Check if already saved
    if not SavedListing.objects.filter(user=request.user, listing=listing).exists():
        SavedListing.objects.create(user=request.user, listing=listing)
        messages.success(request, f"{listing.pokemon.pokemon.name} added to your saved listings!")
    else:
        messages.info(request, "This listing is already in your saved listings.")
    
    return redirect('marketplace:view_listing', listing_id=listing.id)

@login_required
def unsave_listing(request, listing_id):
    """Remove a listing from the user's favorites."""
    listing = get_object_or_404(MarketplaceListing, id=listing_id)
    saved = get_object_or_404(SavedListing, user=request.user, listing=listing)
    
    saved.delete()
    messages.info(request, f"{listing.pokemon.pokemon.name} removed from your saved listings.")
    
    return redirect('marketplace:view_listing', listing_id=listing.id)

@login_required
def search_marketplace(request):
    """Search for Pokemon in the marketplace."""
    query = request.GET.get('q', '')
    pokemon_type = request.GET.get('type', '')
    rarity = request.GET.get('rarity', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    
    # Start with all active listings except user's own
    listings = MarketplaceListing.objects.filter(
        status='active'
    ).exclude(
        seller=request.user
    )
    
    # Apply filters
    if query:
        listings = listings.filter(
            Q(pokemon__pokemon__name__icontains=query) |
            Q(description__icontains=query)
        )
    
    if pokemon_type:
        listings = listings.filter(
            Q(pokemon__pokemon__primary_type=pokemon_type) |
            Q(pokemon__pokemon__secondary_type=pokemon_type)
        )
    
    if rarity:
        listings = listings.filter(pokemon__pokemon__rarity=rarity)
    
    if min_price:
        try:
            min_price = int(min_price)
            listings = listings.filter(price__gte=min_price)
        except ValueError:
            pass
    
    if max_price:
        try:
            max_price = int(max_price)
            listings = listings.filter(price__lte=max_price)
        except ValueError:
            pass
    
    # Get Pokemon types and rarities for filters
    pokemon_types = Pokemon.type_choices
    pokemon_rarities = Pokemon.rarity_choices
    
    context = {
        'listings': listings,
        'pokemon_types': pokemon_types,
        'pokemon_rarities': pokemon_rarities,
        'query': query,
        'selected_type': pokemon_type,
        'selected_rarity': rarity,
        'min_price': min_price,
        'max_price': max_price,
    }
    
    return render(request, 'marketplace/search_results.html', context)
