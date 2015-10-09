from django.http import UnreadablePostError

# This is taken from the Django documentation:
#   https://docs.djangoproject.com/en/1.6/topics/logging/#django.utils.log.CallbackFilter

def skip_unreadable_post(record):
    if record.exc_info:
        exc_type, exc_value = record.exc_info[:2]
        if isinstance(exc_value, UnreadablePostError):
            return False
    return True
