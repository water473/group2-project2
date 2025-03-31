from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import MarketplaceListing, Transaction, SavedListing
from pokemon.models import UserCollection, Pokemon

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
def create_listing(request, pokemon_id):
    """Create a new marketplace listing."""
    user_pokemon = get_object_or_404(UserCollection, id=pokemon_id, user=request.user)
    
    # Check if this Pokemon is already listed
    if MarketplaceListing.objects.filter(pokemon=user_pokemon, status='active').exists():
        messages.error(request, "This Pokemon is already listed in the marketplace!")
        return redirect('pokemon:collection_pokemon_detail', collection_id=pokemon_id)
    
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
            return render(request, 'marketplace/create_listing.html', {'user_pokemon': user_pokemon})
        
        # Create listing
        listing = MarketplaceListing.objects.create(
            seller=request.user,
            pokemon=user_pokemon,
            price=price,
            description=description
        )
        
        messages.success(request, f"{user_pokemon.pokemon.name} listed for {price} coins!")
        return redirect('marketplace:view_listing', listing_id=listing.id)
    
    return render(request, 'marketplace/create_listing.html', {'user_pokemon': user_pokemon})

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
    """Cancel a marketplace listing."""
    listing = get_object_or_404(MarketplaceListing, id=listing_id, seller=request.user, status='active')
    
    listing.status = 'cancelled'
    listing.save()
    
    messages.info(request, f"Listing for {listing.pokemon.pokemon.name} has been cancelled.")
    return redirect('marketplace:my_listings')

@login_required
def purchase(request, listing_id):
    """Purchase a Pokemon from the marketplace."""
    listing = get_object_or_404(MarketplaceListing, id=listing_id, status='active')
    
    # Prevent buying your own listings
    if listing.seller == request.user:
        messages.error(request, "You can't buy your own Pokemon!")
        return redirect('marketplace:view_listing', listing_id=listing.id)
    
    # Check if user has enough coins
    if request.user.profile.coins < listing.price:
        messages.error(request, "You don't have enough coins for this purchase!")
        return redirect('marketplace:view_listing', listing_id=listing.id)
    
    # Process the transaction
    # 1. Create transaction record
    transaction = Transaction.objects.create(
        listing=listing,
        buyer=request.user,
        price_paid=listing.price
    )
    
    # 2. Transfer Pokemon ownership
    pokemon = listing.pokemon
    pokemon.user = request.user
    pokemon.save()
    
    # 3. Transfer coins
    buyer_profile = request.user.profile
    seller_profile = listing.seller.profile
    
    buyer_profile.coins -= listing.price
    seller_profile.coins += listing.price
    
    buyer_profile.save()
    seller_profile.save()
    
    # 4. Update listing status
    listing.status = 'sold'
    listing.save()
    
    messages.success(request, f"You've successfully purchased {pokemon.pokemon.name} for {listing.price} coins!")
    return redirect('pokemon:collection_pokemon_detail', collection_id=pokemon.id)

@login_required
def my_listings(request):
    """View the user's marketplace listings."""
    active_listings = MarketplaceListing.objects.filter(
        seller=request.user,
        status='active'
    ).order_by('-created_at')
    
    sold_listings = MarketplaceListing.objects.filter(
        seller=request.user,
        status='sold'
    ).order_by('-updated_at')
    
    cancelled_listings = MarketplaceListing.objects.filter(
        seller=request.user,
        status='cancelled'
    ).order_by('-updated_at')
    
    context = {
        'active_listings': active_listings,
        'sold_listings': sold_listings,
        'cancelled_listings': cancelled_listings,
    }
    
    return render(request, 'marketplace/my_listings.html', context)

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
