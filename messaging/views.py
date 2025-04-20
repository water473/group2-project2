from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Conversation, Message

@login_required
def inbox(request):
    """View the user's inbox."""
    # Get unread count for the inbox
    unread_count = Message.objects.filter(recipient=request.user, is_read=False).count()
    
    # Get messages for the current folder
    folder = request.GET.get('folder', 'inbox')
    if folder == 'inbox':
        message_list = Message.objects.filter(recipient=request.user)
    elif folder == 'sent':
        message_list = Message.objects.filter(sender=request.user)
    elif folder == 'archived':
        message_list = Message.objects.filter(
            Q(sender=request.user) | Q(recipient=request.user),
            is_archived=True
        )
    else:
        message_list = Message.objects.none()
    
    # Paginate messages
    paginator = Paginator(message_list, 10)
    page_number = request.GET.get('page')
    messages_list = paginator.get_page(page_number)
    
    # Get recent contacts for the sidebar
    recent_contacts = User.objects.filter(
        Q(sent_messages__recipient=request.user) |
        Q(received_messages__sender=request.user)
    ).distinct().order_by('-sent_messages__created_at')[:5]
    
    context = {
        'folder': folder,
        'messages_list': messages_list,
        'unread_count': unread_count,
        'recent_contacts': recent_contacts,
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
def view_message(request, message_id):
    """View a specific message."""
    message = get_object_or_404(
        Message,
        Q(sender=request.user) | Q(recipient=request.user),
        id=message_id
    )
    
    # Mark as read if the current user is the recipient
    if message.recipient == request.user and not message.is_read:
        message.is_read = True
        message.save()
    
    # Determine if this is an inbox or sent message
    message_folder = 'inbox' if message.recipient == request.user else 'sent'
    
    # Get message thread if it exists
    message_thread = Message.objects.filter(
        Q(sender=message.sender, recipient=message.recipient) |
        Q(sender=message.recipient, recipient=message.sender)
    ).exclude(id=message.id).order_by('created_at')
    
    context = {
        'message': message,
        'message_thread': message_thread,
        'message_folder': message_folder,
    }
    
    return render(request, 'messaging/message_detail.html', context)

@login_required
def new_message(request, username=None):
    """Create a new message."""
    if request.method == 'POST':
        recipient_username = request.POST.get('recipient', username)
        recipient = get_object_or_404(User, username=recipient_username)
        parent_message_id = request.POST.get('parent_message_id')
        
        # Don't allow messaging yourself
        if recipient == request.user:
            messages.error(request, "You can't message yourself!")
            return redirect('messaging:inbox')
        
        # Create the message
        Message.objects.create(
            sender=request.user,
            recipient=recipient,
            subject=request.POST.get('subject', ''),
            content=request.POST.get('content', ''),
            parent_message_id=parent_message_id
        )
        
        messages.success(request, 'Message sent successfully!')
        return redirect('messaging:inbox')
    
    # If username is provided, pre-fill the recipient
    recipient = None
    parent_message = None
    if username:
        recipient = get_object_or_404(User, username=username)
    
    # If parent_message_id is provided, get the parent message
    parent_message_id = request.GET.get('parent_message_id')
    if parent_message_id:
        parent_message = get_object_or_404(
            Message,
            Q(sender=request.user) | Q(recipient=request.user),
            id=parent_message_id
        )
        if not recipient:
            recipient = parent_message.sender if parent_message.recipient == request.user else parent_message.recipient
    
    context = {
        'recipient': recipient,
        'parent_message': parent_message,
    }
    
    return render(request, 'messaging/new_message.html', context)

@login_required
def mark_message_read(request, message_id):
    """Mark a message as read."""
    message = get_object_or_404(
        Message,
        recipient=request.user,
        id=message_id
    )
    
    if not message.is_read:
        message.is_read = True
        message.save()
    
    return redirect('messaging:view_message', message_id=message_id)

@login_required
def archive_message(request, message_id):
    """Archive a message."""
    message = get_object_or_404(
        Message,
        Q(sender=request.user) | Q(recipient=request.user),
        id=message_id
    )
    
    message.is_archived = True
    message.save()
    
    messages.success(request, 'Message archived successfully!')
    return redirect('messaging:inbox')

@login_required
def delete_message(request, message_id):
    """Delete a message."""
    message = get_object_or_404(
        Message,
        Q(sender=request.user) | Q(recipient=request.user),
        id=message_id
    )
    
    message.delete()
    
    messages.success(request, 'Message deleted successfully!')
    return redirect('messaging:inbox')

@login_required
def mark_all_read(request):
    """Mark all unread messages as read."""
    try:
        # Mark all unread messages as read
        Message.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        messages.success(request, "All messages marked as read.")
    except Exception as e:
        messages.error(request, f"Error marking messages as read: {str(e)}")
    
    return redirect('messaging:inbox')
