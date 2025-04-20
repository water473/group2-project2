from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import TradeOffer, TradeNotification, TradeHistory
from pokemon.models import UserPokemon
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET

@login_required
def trade_home(request):
    """Trading homepage."""
    # Get recent trades for display
    sent_trades = TradeOffer.objects.filter(sender=request.user).order_by('-created_at')[:5]
    received_trades = TradeOffer.objects.filter(receiver=request.user).order_by('-created_at')[:5]
    
    # Get unread notifications count
    unread_notifications = TradeNotification.objects.filter(
        user=request.user, 
        is_read=False
    ).count()
    
    context = {
        'sent_trades': sent_trades,
        'received_trades': received_trades,
        'unread_notifications': unread_notifications,
    }
    
    return render(request, 'trading/home.html', context)

@login_required
def create_trade(request, username):
    """Create a new trade offer."""
    # Get the receiver
    receiver = get_object_or_404(User, username=username)
    
    # Don't allow trades with yourself
    if receiver == request.user:
        messages.error(request, "You can't trade with yourself!")
        return redirect('trading:home')
    
    if request.method == 'POST':
        # Create a new trade offer
        trade = TradeOffer.objects.create(
            sender=request.user,
            receiver=receiver,
            message=request.POST.get('message', '')
        )
        
        # Add the sender's pokemon to the trade
        for pokemon_id in request.POST.getlist('sender_pokemon'):
            pokemon = get_object_or_404(UserCollection, id=pokemon_id, user=request.user)
            TradeItem.objects.create(
                trade=trade,
                pokemon_offered=pokemon,
                is_sender_item=True
            )
        
        # Add the receiver's pokemon to the trade
        for pokemon_id in request.POST.getlist('receiver_pokemon'):
            pokemon = get_object_or_404(UserCollection, id=pokemon_id, user=receiver)
            TradeItem.objects.create(
                trade=trade,
                pokemon_offered=pokemon,
                is_sender_item=False
            )
        
        # Create a notification for the receiver
        TradeNotification.objects.create(
            user=receiver,
            trade=trade,
            message=f"{request.user.username} has sent you a trade offer!"
        )
        
        messages.success(request, f"Trade offer sent to {receiver.username}!")
        return redirect('trading:view_trade', trade_id=trade.id)
    
    # Get the users' collections for the trade form
    sender_collection = UserCollection.objects.filter(user=request.user)
    receiver_collection = UserCollection.objects.filter(user=receiver)
    
    context = {
        'receiver': receiver,
        'sender_collection': sender_collection,
        'receiver_collection': receiver_collection,
    }
    
    return render(request, 'trading/create_trade.html', context)

@login_required
def create_trade_with_pokemon(request, username, pokemon_id):
    """Create a trade directly from a Pokemon detail page."""
    # Similar to create_trade, but with a specific Pokemon pre-selected
    receiver = get_object_or_404(User, username=username)
    receiver_pokemon = get_object_or_404(UserCollection, id=pokemon_id, user=receiver)
    
    # Don't allow trades with yourself
    if receiver == request.user:
        messages.error(request, "You can't trade with yourself!")
        return redirect('pokemon:collection')
    
    # Get the users' collections for the trade form
    sender_collection = UserCollection.objects.filter(user=request.user)
    
    context = {
        'receiver': receiver,
        'sender_collection': sender_collection,
        'receiver_pokemon': receiver_pokemon,
    }
    
    return render(request, 'trading/create_trade_with_pokemon.html', context)

@login_required
def view_trade(request, trade_id):
    """View details of a specific trade."""
    trade = get_object_or_404(
        TradeOffer,
        id=trade_id,
        sender=request.user
    ) if TradeOffer.objects.filter(id=trade_id, sender=request.user).exists() else get_object_or_404(
        TradeOffer,
        id=trade_id,
        receiver=request.user
    )
    
    # Get the items for this trade
    sender_items = TradeItem.objects.filter(trade=trade, is_sender_item=True)
    receiver_items = TradeItem.objects.filter(trade=trade, is_sender_item=False)
    
    context = {
        'trade': trade,
        'sender_items': sender_items,
        'receiver_items': receiver_items,
        'is_sender': trade.sender == request.user,
    }
    
    return render(request, 'trading/view_trade.html', context)

@login_required
def sent_trades(request):
    """View trades sent by the user."""
    trades = TradeOffer.objects.filter(sender=request.user).order_by('-created_at')
    return render(request, 'trading/sent_trades.html', {'trades': trades})

@login_required
def received_trades(request):
    """View trades received by the user."""
    trades = TradeOffer.objects.filter(receiver=request.user).order_by('-created_at')
    return render(request, 'trading/received_trades.html', {'trades': trades})

@login_required
def accept_trade(request, trade_id):
    """Accept a trade offer."""
    trade = get_object_or_404(TradeOffer, id=trade_id, receiver=request.user, status='pending')
    
    # Get all items in this trade
    sender_items = TradeItem.objects.filter(trade=trade, is_sender_item=True)
    receiver_items = TradeItem.objects.filter(trade=trade, is_sender_item=False)
    
    # Execute the trade (update ownership of all Pokemon)
    for item in sender_items:
        # Transfer ownership from sender to receiver
        item.pokemon_offered.user = request.user
        item.pokemon_offered.save()
    
    for item in receiver_items:
        # Transfer ownership from receiver to sender
        item.pokemon_offered.user = trade.sender
        item.pokemon_offered.save()
    
    # Update trade status
    trade.status = 'accepted'
    trade.save()
    
    # Create notifications
    TradeNotification.objects.create(
        user=trade.sender,
        trade=trade,
        message=f"{request.user.username} has accepted your trade offer!"
    )
    
    messages.success(request, "Trade accepted successfully!")
    return redirect('trading:view_trade', trade_id=trade.id)

@login_required
def reject_trade(request, trade_id):
    """Reject a trade offer."""
    trade = get_object_or_404(TradeOffer, id=trade_id, receiver=request.user, status='pending')
    
    # Update trade status
    trade.status = 'rejected'
    trade.save()
    
    # Create notification
    TradeNotification.objects.create(
        user=trade.sender,
        trade=trade,
        message=f"{request.user.username} has rejected your trade offer."
    )
    
    messages.info(request, "Trade rejected.")
    return redirect('trading:received_trades')

@login_required
def cancel_trade(request, trade_id):
    """Cancel a pending trade offer."""
    trade = get_object_or_404(TradeOffer, id=trade_id, sender=request.user, status='pending')
    
    # Update trade status
    trade.status = 'cancelled'
    trade.save()
    
    # Create notification
    TradeNotification.objects.create(
        user=trade.receiver,
        trade=trade,
        message=f"{request.user.username} has cancelled their trade offer."
    )
    
    messages.info(request, "Trade cancelled.")
    return redirect('trading:sent_trades')

@login_required
def trade_notifications(request):
    """View all trade notifications."""
    notifications = TradeNotification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'trading/notifications.html', {'notifications': notifications})

@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read."""
    notification = get_object_or_404(TradeNotification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    
    return redirect('trading:notifications')

@login_required
def trade_offers(request):
    """View all trade offers for the current user."""
    # Get sent offers
    sent_offers = TradeOffer.objects.filter(
        sender=request.user
    ).select_related('sender', 'recipient').prefetch_related(
        'offered_pokemon', 'requested_pokemon'
    ).order_by('-created_at')
    
    # Get received offers
    received_offers = TradeOffer.objects.filter(
        recipient=request.user
    ).select_related('sender', 'recipient').prefetch_related(
        'offered_pokemon', 'requested_pokemon'
    ).order_by('-created_at')
    
    # Filter by status if specified
    status = request.GET.get('status')
    if status:
        sent_offers = sent_offers.filter(status=status)
        received_offers = received_offers.filter(status=status)
    
    context = {
        'sent_offers': sent_offers,
        'received_offers': received_offers,
        'status': status,
    }
    return render(request, 'trading/trade_offers.html', context)

@login_required
def create_trade_offer(request, username=None):
    """Create a new trade offer."""
    if request.method == 'POST':
        try:
            # Get recipient ID from POST data
            recipient_id = request.POST.get('recipient')
            if not recipient_id:
                messages.error(request, "Please select a user to trade with.")
                return redirect('trading:trade_offers')
            
            # Get recipient user
            recipient = get_object_or_404(User, id=recipient_id)
            
            # Don't allow trading with yourself
            if recipient == request.user:
                messages.error(request, "You cannot trade with yourself.")
                return redirect('trading:trade_offers')
            
            # Get offered and requested Pokémon
            offered_pokemon_ids = request.POST.getlist('offered_pokemon')
            requested_pokemon_ids = request.POST.getlist('requested_pokemon')
            
            # Validate that user owns the offered Pokémon
            offered_pokemon = UserPokemon.objects.filter(
                id__in=offered_pokemon_ids,
                user=request.user
            )
            if len(offered_pokemon) != len(offered_pokemon_ids):
                messages.error(request, "You don't own all the Pokémon you're trying to offer.")
                return redirect('trading:trade_offers')
            
            # Validate that recipient owns the requested Pokémon
            requested_pokemon = UserPokemon.objects.filter(
                id__in=requested_pokemon_ids,
                user=recipient
            )
            if len(requested_pokemon) != len(requested_pokemon_ids):
                messages.error(request, f"{recipient.username} doesn't own all the Pokémon you're requesting.")
                return redirect('trading:trade_offers')
            
            # Create the trade offer
            trade_offer = TradeOffer.objects.create(
                sender=request.user,
                recipient=recipient,
                message=request.POST.get('message', '')
            )
            
            # Add Pokémon to the trade
            trade_offer.offered_pokemon.set(offered_pokemon)
            trade_offer.requested_pokemon.set(requested_pokemon)
            
            messages.success(request, "Trade offer sent successfully!")
            return redirect('trading:trade_offer_detail', offer_id=trade_offer.id)
            
        except Exception as e:
            messages.error(request, f"Error creating trade offer: {str(e)}")
            return redirect('trading:trade_offers')
    
    # If username is provided, pre-fill the recipient
    recipient = None
    if username:
        recipient = get_object_or_404(User, username=username)
    
    # Get user's Pokémon that aren't in active trades
    user_pokemon = UserPokemon.objects.filter(
        user=request.user,
        is_for_sale=False
    ).select_related('card')
    
    # Get available users to trade with (excluding self)
    available_users = User.objects.exclude(id=request.user.id)
    
    context = {
        'recipient': recipient,
        'user_pokemon': user_pokemon,
        'available_users': available_users
    }
    return render(request, 'trading/create_trade_offer.html', context)

@login_required
def trade_offer_detail(request, offer_id):
    """View details of a specific trade offer."""
    trade_offer = get_object_or_404(
        TradeOffer.objects.select_related('sender', 'recipient').prefetch_related(
            'offered_pokemon', 'requested_pokemon'
        ),
        id=offer_id
    )
    
    # Ensure user is either sender or recipient
    if request.user not in [trade_offer.sender, trade_offer.recipient]:
        messages.error(request, "You don't have permission to view this trade offer.")
        return redirect('trading:trade_offers')
    
    # Determine if user is the sender or recipient
    is_sender = request.user == trade_offer.sender
    is_recipient = request.user == trade_offer.recipient
    
    if request.method == 'POST':
        if is_recipient and trade_offer.status == 'pending':
            response = request.POST.get('response')
            message = request.POST.get('message', '')
            
            if response == 'accept':
                # Transfer Pokémon from sender to recipient
                for pokemon in trade_offer.offered_pokemon.all():
                    pokemon.user = request.user
                    pokemon.save()
                
                # Transfer Pokémon from recipient to sender
                for pokemon in trade_offer.requested_pokemon.all():
                    pokemon.user = trade_offer.sender
                    pokemon.save()
                
                # Update trade status
                trade_offer.status = 'accepted'
                trade_offer.save()
                
                # Create notification for sender
                TradeNotification.objects.create(
                    user=trade_offer.sender,
                    trade_offer=trade_offer,
                    notification_type='offer_accepted'
                )
                
                messages.success(request, "Trade offer accepted successfully!")
                return redirect('trading:trade_offers')
                
            elif response == 'decline':
                # Update trade status
                trade_offer.status = 'declined'
                trade_offer.save()
                
                # Create notification for sender
                TradeNotification.objects.create(
                    user=trade_offer.sender,
                    trade_offer=trade_offer,
                    notification_type='offer_declined'
                )
                
                messages.success(request, "Trade offer declined.")
                return redirect('trading:trade_offers')
                
            elif response == 'counter':
                # Redirect to counter offer page
                return redirect('trading:counter_trade_offer', offer_id=offer_id)
                
        elif is_sender and trade_offer.status == 'pending':
            action = request.POST.get('action')
            if action == 'cancel':
                # Update trade status
                trade_offer.status = 'cancelled'
                trade_offer.save()
                
                # Create notification for recipient
                TradeNotification.objects.create(
                    user=trade_offer.recipient,
                    trade_offer=trade_offer,
                    notification_type='trade_cancelled'
                )
                
                messages.success(request, "Trade offer cancelled.")
                return redirect('trading:trade_offers')
    
    context = {
        'trade_offer': trade_offer,
        'is_sender': is_sender,
        'is_recipient': is_recipient,
        'can_respond': is_recipient and trade_offer.status == 'pending',
        'can_cancel': is_sender and trade_offer.status == 'pending'
    }
    return render(request, 'trading/trade_offer_detail.html', context)

@login_required
def accept_trade_offer(request, offer_id):
    """Accept a trade offer."""
    trade_offer = get_object_or_404(
        TradeOffer.objects.select_related('sender', 'recipient').prefetch_related(
            'offered_pokemon', 'requested_pokemon'
        ),
        id=offer_id
    )
    
    # Ensure user is the recipient
    if request.user != trade_offer.recipient:
        messages.error(request, "You don't have permission to accept this trade offer.")
        return redirect('trading:trade_offers')
    
    # Ensure trade is still pending
    if trade_offer.status != 'pending':
        messages.error(request, "This trade offer is no longer pending.")
        return redirect('trading:trade_offer_detail', offer_id=offer_id)
    
    try:
        # Transfer Pokémon from sender to recipient
        for pokemon in trade_offer.offered_pokemon.all():
            pokemon.user = request.user
            pokemon.save()
        
        # Transfer Pokémon from recipient to sender
        for pokemon in trade_offer.requested_pokemon.all():
            pokemon.user = trade_offer.sender
            pokemon.save()
        
        # Update trade status
        trade_offer.status = 'accepted'
        trade_offer.save()
        
        # Create notification for sender
        TradeNotification.objects.create(
            user=trade_offer.sender,
            trade_offer=trade_offer,
            notification_type='offer_accepted'
        )
        
        messages.success(request, "Trade offer accepted successfully!")
    except Exception as e:
        messages.error(request, f"Error accepting trade offer: {str(e)}")
    
    return redirect('trading:trade_offers')

@login_required
def decline_trade_offer(request, offer_id):
    """Decline a trade offer."""
    trade_offer = get_object_or_404(
        TradeOffer.objects.select_related('sender', 'recipient'),
        id=offer_id
    )
    
    # Ensure user is the recipient
    if request.user != trade_offer.recipient:
        messages.error(request, "You don't have permission to decline this trade offer.")
        return redirect('trading:trade_offers')
    
    # Ensure trade is still pending
    if trade_offer.status != 'pending':
        messages.error(request, "This trade offer is no longer pending.")
        return redirect('trading:trade_offer_detail', offer_id=offer_id)
    
    try:
        # Update trade status
        trade_offer.status = 'declined'
        trade_offer.save()
        
        # Create notification for sender
        TradeNotification.objects.create(
            user=trade_offer.sender,
            trade_offer=trade_offer,
            notification_type='offer_declined'
        )
        
        messages.success(request, "Trade offer declined.")
    except Exception as e:
        messages.error(request, f"Error declining trade offer: {str(e)}")
    
    return redirect('trading:trade_offers')

@login_required
def counter_trade_offer(request, offer_id):
    """Create a counter offer based on an existing trade offer."""
    original_offer = get_object_or_404(
        TradeOffer.objects.select_related('sender', 'recipient').prefetch_related(
            'offered_pokemon', 'requested_pokemon'
        ),
        id=offer_id
    )
    
    # Ensure user is the recipient
    if request.user != original_offer.recipient:
        messages.error(request, "You don't have permission to counter this trade offer.")
        return redirect('trading:trade_offers')
    
    # Ensure trade is still pending
    if original_offer.status != 'pending':
        messages.error(request, "This trade offer is no longer pending.")
        return redirect('trading:trade_offer_detail', offer_id=offer_id)
    
    if request.method == 'POST':
        try:
            # Get offered and requested Pokémon
            offered_pokemon_ids = request.POST.getlist('offered_pokemon')
            requested_pokemon_ids = request.POST.getlist('requested_pokemon')
            
            # Validate that user owns the offered Pokémon
            offered_pokemon = UserPokemon.objects.filter(
                id__in=offered_pokemon_ids,
                user=request.user
            )
            if len(offered_pokemon) != len(offered_pokemon_ids):
                messages.error(request, "You don't own all the Pokémon you're trying to offer.")
                return redirect('trading:trade_offer_detail', offer_id=offer_id)
            
            # Validate that sender owns the requested Pokémon
            requested_pokemon = UserPokemon.objects.filter(
                id__in=requested_pokemon_ids,
                user=original_offer.sender
            )
            if len(requested_pokemon) != len(requested_pokemon_ids):
                messages.error(request, f"{original_offer.sender.username} doesn't own all the Pokémon you're requesting.")
                return redirect('trading:trade_offer_detail', offer_id=offer_id)
            
            # Create the counter offer
            counter_offer = TradeOffer.objects.create(
                sender=request.user,
                recipient=original_offer.sender,
                message=request.POST.get('message', '')
            )
            
            # Add Pokémon to the counter offer
            counter_offer.offered_pokemon.set(offered_pokemon)
            counter_offer.requested_pokemon.set(requested_pokemon)
            
            # Update original offer status
            original_offer.status = 'declined'
            original_offer.save()
            
            # Create notification for original sender
            TradeNotification.objects.create(
                user=original_offer.sender,
                trade_offer=counter_offer,
                notification_type='offer_received'
            )
            
            messages.success(request, "Counter offer sent successfully!")
            return redirect('trading:trade_offer_detail', offer_id=counter_offer.id)
            
        except Exception as e:
            messages.error(request, f"Error creating counter offer: {str(e)}")
            return redirect('trading:trade_offer_detail', offer_id=offer_id)
    
    # Get user's Pokémon that aren't in active trades
    user_pokemon = UserPokemon.objects.filter(
        user=request.user,
        is_for_sale=False
    ).select_related('card')
    
    # Get sender's Pokémon that aren't in active trades
    sender_pokemon = UserPokemon.objects.filter(
        user=original_offer.sender,
        is_for_sale=False
    ).select_related('card')
    
    context = {
        'original_offer': original_offer,
        'user_pokemon': user_pokemon,
        'sender_pokemon': sender_pokemon
    }
    return render(request, 'trading/counter_trade_offer.html', context)

@login_required
def trade_history(request):
    """View trade history for the current user."""
    # Get completed trades where user was either sender or recipient
    trades = TradeHistory.objects.filter(
        trade_offer__sender=request.user
    ) | TradeHistory.objects.filter(
        trade_offer__recipient=request.user
    )
    
    trades = trades.select_related(
        'trade_offer__sender',
        'trade_offer__recipient'
    ).prefetch_related(
        'trade_offer__offered_pokemon',
        'trade_offer__requested_pokemon'
    ).order_by('-completed_at')
    
    # Filter by status if specified
    status = request.GET.get('status')
    if status:
        trades = trades.filter(status=status)
    
    # Paginate results
    paginator = Paginator(trades, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status': status,
    }
    return render(request, 'trading/trade_history.html', context)

@login_required
def trade_history_detail(request, trade_id):
    """View details of a specific trade in history."""
    trade = get_object_or_404(
        TradeHistory.objects.select_related(
            'trade_offer__sender',
            'trade_offer__recipient'
        ).prefetch_related(
            'trade_offer__offered_pokemon',
            'trade_offer__requested_pokemon'
        ),
        id=trade_id
    )
    
    # Ensure user was part of the trade
    if request.user not in [trade.trade_offer.sender, trade.trade_offer.recipient]:
        messages.error(request, "You don't have permission to view this trade history.")
        return redirect('trading:trade_history')
    
    context = {
        'trade': trade,
        'is_sender': request.user == trade.trade_offer.sender,
    }
    return render(request, 'trading/trade_history_detail.html', context)

@login_required
def trade_notifications(request):
    """View trade notifications for the current user."""
    notifications = TradeNotification.objects.filter(
        user=request.user
    ).select_related(
        'trade_offer__sender',
        'trade_offer__recipient'
    ).order_by('-created_at')
    
    # Filter by read status if specified
    is_read = request.GET.get('is_read')
    if is_read is not None:
        notifications = notifications.filter(is_read=is_read.lower() == 'true')
    
    # Paginate results
    paginator = Paginator(notifications, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'is_read': is_read,
    }
    return render(request, 'trading/trade_notifications.html', context)

@login_required
def mark_notifications_read(request):
    """Mark all unread trade notifications as read."""
    if request.method == 'POST':
        try:
            TradeNotification.objects.filter(
                user=request.user,
                is_read=False
            ).update(is_read=True)
            messages.success(request, "All notifications marked as read.")
        except Exception as e:
            messages.error(request, f"Error marking notifications as read: {str(e)}")
    
    return redirect('trading:trade_notifications')

@require_GET
@login_required
def get_user_pokemon(request, user_id):
    """API endpoint to get a user's Pokémon collection."""
    try:
        # Get the user's Pokémon that aren't in active trades
        pokemon = UserPokemon.objects.filter(
            user_id=user_id,
            is_for_sale=False
        ).select_related('card').values(
            'id',
            'nickname',
            'card__name',
            'card__image_url'
        )
        
        return JsonResponse(list(pokemon), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def cancel_trade_offer(request, offer_id):
    """Cancel a trade offer."""
    trade_offer = get_object_or_404(
        TradeOffer.objects.select_related('sender', 'recipient'),
        id=offer_id
    )
    
    # Ensure user is the sender
    if request.user != trade_offer.sender:
        messages.error(request, "You don't have permission to cancel this trade offer.")
        return redirect('trading:trade_offers')
    
    # Ensure trade is still pending
    if trade_offer.status != 'pending':
        messages.error(request, "This trade offer is no longer pending.")
        return redirect('trading:trade_offer_detail', offer_id=offer_id)
    
    try:
        # Update trade status
        trade_offer.status = 'cancelled'
        trade_offer.save()
        
        # Create notification for recipient
        TradeNotification.objects.create(
            user=trade_offer.recipient,
            trade_offer=trade_offer,
            notification_type='trade_cancelled'
        )
        
        messages.success(request, "Trade offer cancelled.")
    except Exception as e:
        messages.error(request, f"Error cancelling trade offer: {str(e)}")
    
    return redirect('trading:trade_offers')
