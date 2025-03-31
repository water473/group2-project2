from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from .models import Conversation, Message

@login_required
def inbox(request):
    """User's message inbox showing all conversations."""
    # Get all conversations the user is participating in
    conversations = Conversation.objects.filter(participants=request.user)
    
    # Calculate unread message counts for each conversation
    for conversation in conversations:
        conversation.unread_count = Message.objects.filter(
            conversation=conversation,
            sender__in=conversation.participants.exclude(id=request.user.id),
            is_read=False
        ).count()
    
    context = {
        'conversations': conversations,
    }
    
    return render(request, 'messaging/inbox.html', context)

@login_required
def conversation(request, conversation_id):
    """View a specific conversation."""
    # Get the conversation and verify the user is a participant
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )
    
    # Get all messages in this conversation
    messages_list = Message.objects.filter(conversation=conversation).order_by('timestamp')
    
    # Mark unread messages as read
    for msg in messages_list:
        if not msg.is_read and msg.sender != request.user:
            msg.is_read = True
            msg.save()
    
    # Get other participants for display
    other_participants = conversation.participants.exclude(id=request.user.id)
    
    context = {
        'conversation': conversation,
        'messages': messages_list,
        'other_participants': other_participants,
    }
    
    return render(request, 'messaging/conversation.html', context)

@login_required
def new_conversation(request, username):
    """Start a new conversation with another user."""
    other_user = get_object_or_404(User, username=username)
    
    # Don't allow messaging yourself
    if other_user == request.user:
        messages.error(request, "You can't message yourself!")
        return redirect('messaging:inbox')
    
    # Check if a conversation already exists between these users
    existing_conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=other_user
    ).first()
    
    if existing_conversation:
        # If a conversation exists, redirect to it
        return redirect('messaging:conversation', conversation_id=existing_conversation.id)
    
    # Create a new conversation
    new_conversation = Conversation.objects.create()
    new_conversation.participants.add(request.user, other_user)
    
    context = {
        'conversation': new_conversation,
        'other_user': other_user,
    }
    
    return render(request, 'messaging/new_conversation.html', context)

@login_required
def send_message(request, conversation_id):
    """Send a message in a conversation."""
    # Get the conversation and verify the user is a participant
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        
        if content:
            # Create the message
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
            
            # Update the conversation's last activity timestamp
            conversation.save()  # This will update updated_at due to auto_now=True
        
    return redirect('messaging:conversation', conversation_id=conversation.id)

@login_required
def mark_message_read(request, message_id):
    """Mark a specific message as read."""
    message = get_object_or_404(
        Message,
        id=message_id,
        conversation__participants=request.user
    )
    
    if message.sender != request.user:
        message.is_read = True
        message.save()
    
    return redirect('messaging:conversation', conversation_id=message.conversation.id)
