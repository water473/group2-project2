from django import template

register = template.Library()

@register.filter
def status_color(status):
    """Return the appropriate Bootstrap color class for a trade status."""
    colors = {
        'pending': 'warning',
        'accepted': 'success',
        'declined': 'danger',
        'cancelled': 'secondary',
        'completed': 'info'
    }
    return colors.get(status, 'secondary') 