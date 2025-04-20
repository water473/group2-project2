from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile
from pokemon.models import Pokemon, UserCollection
import random

def register(request):
    """Register a new user and assign initial Pokemon."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Assign random Pokemon to the new user
            # This is a placeholder - you'll need to integrate with the Pokemon API
            # or have a database of Pokemon to assign from
            starter_pokemon = assign_starter_pokemon(user)
            
            messages.success(request, f'Account created successfully! You received {len(starter_pokemon)} starter Pokemon.')
            return redirect('login')
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
def view_profile(request):
    """View the logged-in user's profile."""
    return render(request, 'accounts/profile.html', {'profile_user': request.user})

@login_required
def edit_profile(request):
    """Edit user profile."""
    if request.method == 'POST':
        # Update profile
        profile = request.user.profile
        
        # Update bio
        profile.bio = request.POST.get('bio', '')
        
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']
        
        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('accounts:profile')
    
    return render(request, 'accounts/edit_profile.html')

def view_user_profile(request, username):
    """View another user's profile."""
    user = get_object_or_404(User, username=username)
    return render(request, 'accounts/user_profile.html', {'profile_user': user})
