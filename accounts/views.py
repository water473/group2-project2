from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile
from pokemon.models import Pokemon, UserCollection, UserPokemon
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

            # Assign random Pokemon to the new user
            starter_pokemon = assign_starter_pokemon(user)

            messages.success(request,
                             f'Account created successfully! You received {len(starter_pokemon)} starter Pokemon.')
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
    # This is a placeholder function
    # In a real implementation, you would:
    # 1. Query available Pokemon from your database or API
    # 2. Select a random subset (e.g., 3-5 Pokemon)
    # 3. Create UserCollection entries for each Pokemon
    
    # For now, we'll just use dummy logic
    starter_pokemon = []
    
    # Assuming we have Pokemon in the database
    # If not, this would need to be adjusted when integrating with the Pokemon API
    all_pokemon = Pokemon.objects.all()
    if all_pokemon.exists():
        # Select 3 random Pokemon
        random_pokemon = random.sample(list(all_pokemon), min(3, all_pokemon.count()))
        
        # Add to user's collection
        for pokemon in random_pokemon:
            user_pokemon = UserCollection.objects.create(
                user=user,
                pokemon=pokemon
            )
            starter_pokemon.append(user_pokemon)
    
    return starter_pokemon

@login_required
def profile(request, username=None):
    # If no username is provided, show the current user's profile
    if username is None:
        profile_user = request.user
    else:
        profile_user = get_object_or_404(User, username=username)
    
    # Get trading statistics
    trade_stats = {
        'total_trades': TradeOffer.objects.filter(
            status='completed',
            sender=profile_user
        ).count() + TradeOffer.objects.filter(
            status='completed',
            recipient=profile_user
        ).count(),
        'successful_trades': TradeOffer.objects.filter(
            status='completed',
            sender=profile_user
        ).count()
    }
    
    # Get recent trades
    recent_trades = TradeOffer.objects.filter(
        sender=profile_user
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
        ).values('price_paid').aggregate(total=models.Sum('price_paid'))['total'] or 0
    }
    
    # Get active listings
    active_listings = MarketplaceListing.objects.filter(
        seller=profile_user,
        status='active'
    ).select_related('pokemon', 'pokemon__card').order_by('-created_at')[:3]
    
    # Get recent transactions
    recent_transactions = Transaction.objects.filter(
        models.Q(listing__seller=profile_user) | models.Q(buyer=profile_user)
    ).select_related(
        'listing',
        'listing__pokemon',
        'listing__pokemon__card',
        'listing__seller',
        'buyer'
    ).order_by('-transaction_date')[:5]
    
    context = {
        'profile_user': profile_user,
        'trade_stats': trade_stats,
        'recent_trades': recent_trades,
        'market_stats': market_stats,
        'active_listings': active_listings,
        'recent_transactions': recent_transactions,
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
