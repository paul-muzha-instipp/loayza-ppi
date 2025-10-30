"""
WSGI config for trabajopaulmuzha project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# deberia seguir la misma direccion manageTask.settings como wsgi.py y el archivo manage .py
#os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trabajopaulmuzha.settings')

#CORREGIDO
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'manageTask.settings')

application = get_wsgi_application()
