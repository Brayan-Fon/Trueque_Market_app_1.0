"""
WSGI config for TruequeMarket project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TruequeMarket.settings')

application = get_wsgi_application()

# Auto-migración segura para bases de datos nuevas o de respaldo en Render
try:
    from django.core.management import call_command
    call_command('migrate', interactive=False, verbosity=1)
    from django.contrib.auth.models import User
    if not User.objects.filter(username='admin_trueque').exists():
        User.objects.create_superuser('admin_trueque', 'admin@trueque.com', 'Admin12345!')
except Exception as _wsgi_err:
    print(f"[WSGI INIT WARNING] {_wsgi_err}")
