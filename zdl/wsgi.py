"""
WSGI config for zdl project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os

import os
# import sys
# root = os.path.dirname(__file__)
# sys.path.insert(0, os.path.join(root, '..', 'site-packages'))
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eorder.settings")

import sys
sys.path.append('/usr/lib/python2.7/site-packages')
sys.path.append('/usr/lib64/python2.7/site-packages')



from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zdl.settings")

application = get_wsgi_application()
