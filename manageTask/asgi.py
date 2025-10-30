"""
ASGI config for trabajopaulmuzha project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# Tenias "trabajopaulmuzha" no concuerda, 
# deberia seguir la misma direccion manageTask.settings como wsgi.py y el archivo manage .py
#os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trabajopaulmuzha.settings')

#CORREGIDO
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'manageTask.settings')

application = get_asgi_application()
