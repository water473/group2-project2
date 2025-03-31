from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('conversation/<int:conversation_id>/', views.conversation, name='conversation'),
    path('new/<str:username>/', views.new_conversation, name='new_conversation'),
    path('send/<int:conversation_id>/', views.send_message, name='send_message'),
    path('mark-read/<int:message_id>/', views.mark_message_read, name='mark_message_read'),
] 