def unread_notifications_count(request):
    """Provide unread notifications count to all templates."""
    try:
        from .models import Notification
        count = Notification.objects.filter(is_read=False).count()
    except Exception:
        # If Notification model doesn't exist or table not created, return 0
        count = 0
    return {'unread_notifications_count': count}


