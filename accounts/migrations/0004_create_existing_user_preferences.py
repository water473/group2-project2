from django.db import migrations

def create_notification_preferences(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    NotificationPreferences = apps.get_model('accounts', 'NotificationPreferences')
    
    # Create preferences for all existing users who don't have them
    for user in User.objects.all():
        NotificationPreferences.objects.get_or_create(
            user=user,
            defaults={
                'trading_notifications': True,
                'marketplace_notifications': True
            }
        )

def reverse_notification_preferences(apps, schema_editor):
    NotificationPreferences = apps.get_model('accounts', 'NotificationPreferences')
    NotificationPreferences.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0003_notificationpreferences'),
    ]

    operations = [
        migrations.RunPython(create_notification_preferences, reverse_notification_preferences),
    ] 