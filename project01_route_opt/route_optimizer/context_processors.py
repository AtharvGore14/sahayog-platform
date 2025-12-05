from .models import Notification


def unread_notifications_count(request):
    """Provide unread notifications count to all templates."""
    try:
        count = Notification.objects.filter(is_read=False).count()
    except Exception:
        count = 0
    return {'unread_notifications_count': count}


