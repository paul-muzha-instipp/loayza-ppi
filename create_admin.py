import os
import django

# Configuracion del entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'manageTask.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

# datos de acceso
username = 'admin_loayza'
email = 'admin@almacenesloayza.com'
password = 'muzha.12345' # contraseña

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f"ÉXITO: Superusuario '{username}' creado.")
else:
    print(f"AVISO: El usuario '{username}' ya existe.")