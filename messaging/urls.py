from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('message/<int:message_id>/', views.view_message, name='view_message'),
    path('new/', views.new_message, name='new_message'),
    path('new/<str:username>/', views.new_message, name='new_message_to_user'),
    path('mark-read/<int:message_id>/', views.mark_message_read, name='mark_message_read'),
    path('archive/<int:message_id>/', views.archive_message, name='archive_message'),
    path('delete/<int:message_id>/', views.delete_message, name='delete_message'),
] 