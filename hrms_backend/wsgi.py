"""
WSGI config for hrms_backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys

# Calculate and insert the project root into sys.path
parent = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(parent, '..'))
sys.path.insert(0, project_root)

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms_backend.settings')

application = get_wsgi_application()
