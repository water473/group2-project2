from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import TradeOffer, TradeItem, TradeNotification
from pokemon.models import UserCollection

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
