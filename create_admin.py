import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TruequeMarket.settings')
django.setup()

from django.contrib.auth.models import User

if not User.objects.filter(username='admin_trueque').exists():
    User.objects.create_superuser('admin_trueque', 'admin@trueque.com', 'Admin12345!')
    print("Superuser created successfully!")
else:
    print("Superuser already exists.")
