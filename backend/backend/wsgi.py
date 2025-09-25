"""
WSGI config for backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
import threading
import time
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

application = get_wsgi_application()

# pylint: disable=C0413
from django.utils.timezone import now
from rest_framework_simplejwt.tokens import OutstandingToken


def cleanup_task():
    """Thread function to clean up expired refresh tokens."""
    while True:
        expired_tokens = OutstandingToken.objects.filter(expires_at__lt=now())
        count = expired_tokens.count()
        expired_tokens.delete()
        print(f"Deleted {count} expired refresh tokens")

        time.sleep(21600)  # Wait for 6 hours (21600 seconds)


# Start background thread
thread = threading.Thread(target=cleanup_task, daemon=True)
thread.start()
