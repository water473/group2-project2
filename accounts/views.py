from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile, NotificationPreferences
from pokemon.models import Pokemon, UserCollection, UserPokemon, WishlistItem, PokemonCard
from .forms import ProfileForm
import random
from django.db.models import Count, Sum
from django.db.models import Q
from trading.models import TradeOffer
from marketplace.models import MarketplaceListing, Transaction
from django.db import models


def register(request):
    """Register a new user and assign initial Pokemon."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            print(f"Creating account for user: {user.username}")  # Debug log

            messages.success(request,
                             'Account created successfully! You received 6 starter Pokemon.')
            return redirect('login')
        else:
            # Add warnings for form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.warning(request, f"{field.capitalize()}: {error}")
    else:
        form = UserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})

def assign_starter_pokemon(user):
    """Assign starter Pokemon to a new user."""
    starter_pokemon = []
    print(f"Starting Pokemon assignment for user: {user.username}")  # Debug log
    
    # Get all available Pokemon cards
    all_pokemon = PokemonCard.objects.all()
    if all_pokemon.exists():
        # Select 6 random Pokemon
        NUM_POKEMON_START = 6
        random_pokemon = random.sample(list(all_pokemon), min(NUM_POKEMON_START, all_pokemon.count()))
        print(f"Selected {len(random_pokemon)} random Pokemon")  # Debug log
        
        # Add to user's collection
        for pokemon in random_pokemon:
            user_pokemon = UserPokemon.objects.create(
                user=user,
                card=pokemon
            )
            starter_pokemon.append(user_pokemon)
            print(f"Added {pokemon.name} to {user.username}'s collection")  # Debug log
    
    print(f"Completed Pokemon assignment for {user.username}. Total assigned: {len(starter_pokemon)}")  # Debug log
    return starter_pokemon

@login_required
def profile(request, username=None):
    # If no username is provided, show the current user's profile
    if username is None:
        profile_user = request.user
    else:
        profile_user = get_object_or_404(User, username=username)
    
    # Get collection statistics
    user_pokemon = UserPokemon.objects.filter(user=profile_user)
    collection_stats = {
        'total_pokemon': user_pokemon.count(),
        'unique_pokemon': user_pokemon.values('card__name').distinct().count(),
        'collection_value': user_pokemon.aggregate(total=Sum('card__base_value'))['total'] or 0,
    }

    # Calculate type distribution
    type_distribution = {}
    for pokemon in user_pokemon:
        if pokemon.card.types:
            for type_name in pokemon.card.types:
                type_distribution[type_name] = type_distribution.get(type_name, 0) + 1
    
    # Convert to percentages
    if type_distribution:
        total = sum(type_distribution.values())
        type_distribution = {k: (v / total) * 100 for k, v in type_distribution.items()}
    
    collection_stats['type_distribution'] = type_distribution

    # Find rarest pokemon
    rarest_pokemon = None
    if user_pokemon.exists():
        rarest_pokemon = user_pokemon.order_by('-card__base_value').first()
        if rarest_pokemon:
            collection_stats['rarest_pokemon'] = {
                'name': rarest_pokemon.card.name,
                'rarity': rarest_pokemon.card.rarity
            }
    
    # Get trading statistics
    trade_stats = {
        'total_trades': TradeOffer.objects.filter(
            Q(sender=profile_user) | Q(recipient=profile_user)
        ).count(),
        'successful_trades': TradeOffer.objects.filter(
            Q(sender=profile_user) | Q(recipient=profile_user),
            status='completed'
        ).count()
    }
    
    # Get recent trades
    recent_trades = TradeOffer.objects.filter(
        Q(sender=profile_user) | Q(recipient=profile_user)
    ).order_by('-updated_at')[:5]
    
    # Get marketplace statistics
    market_stats = {
        'total_sold': MarketplaceListing.objects.filter(
            seller=profile_user,
            status='sold'
        ).count(),
        'total_purchased': MarketplaceListing.objects.filter(
            buyer=profile_user,
            status='sold'
        ).count(),
        'total_value': Transaction.objects.filter(
            listing__seller=profile_user
        ).aggregate(total=Sum('price_paid'))['total'] or 0
    }
    
    # Get active listings
    active_listings = MarketplaceListing.objects.filter(
        seller=profile_user,
        status='active'
    ).select_related('pokemon', 'pokemon__card').order_by('-created_at')[:3]
    
    # Get recent transactions
    recent_transactions = Transaction.objects.filter(
        Q(listing__seller=profile_user) | Q(buyer=profile_user)
    ).select_related(
        'listing',
        'listing__pokemon',
        'listing__pokemon__card',
        'listing__seller',
        'buyer'
    ).order_by('-transaction_date')[:5]
    
    context = {
        'profile_user': profile_user,
        'collection_stats': collection_stats,
        'trade_stats': trade_stats,
        'recent_trades': recent_trades,
        'market_stats': market_stats,
        'active_listings': active_listings,
        'recent_transactions': recent_transactions,
        'wishlist_items': WishlistItem.objects.filter(user=profile_user).select_related('pokemon_card'),
    }
    
    return render(request, 'accounts/profile.html', context)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user.profile)
    
    return render(request, 'accounts/edit_profile.html', {'form': form})

def view_user_profile(request, username):
    """View another user's profile."""
    user = get_object_or_404(User, username=username)
    return render(request, 'accounts/user_profile.html', {'profile_user': user})

@login_required
def notification_preferences(request):
    """View and update notification preferences."""
    if request.method == 'POST':
        preferences = request.user.notification_preferences
        preferences.trading_notifications = request.POST.get('trading_notifications') == 'on'
        preferences.marketplace_notifications = request.POST.get('marketplace_notifications') == 'on'
        preferences.save()
        messages.success(request, 'Notification preferences updated successfully.')
        return redirect('accounts:notification_preferences')

    return render(request, 'accounts/notification_preferences.html')
