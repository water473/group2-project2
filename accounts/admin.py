from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'join_date', 'coins')
    search_fields = ('user__username', 'bio')
    list_filter = ('join_date',)
