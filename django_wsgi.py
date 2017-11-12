
#!/usr/bin/env python
# coding: utf-8


import os


import sys


# UTF8

reload(sys)

sys.setdefaultencoding('utf8')


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zdl.settings")


from django.core.handlers.wsgi import WSGIHandler

application = WSGIHandler()

#no use