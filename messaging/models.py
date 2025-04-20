from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings

class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        participant_names = ', '.join([user.username for user in self.participants.all()])
        return f"Conversation between {participant_names}"
    
    class Meta:
        ordering = ['-updated_at']

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages',
        default=1  # Default to first user (usually admin)
    )
    subject = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    parent_message = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    related_transaction = models.ForeignKey(
        'marketplace.Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_messages'
    )
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Message from {self.sender.username} to {self.recipient.username}"
