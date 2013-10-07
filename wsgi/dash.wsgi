import os
import sys

sys.path.append('/home/mlapora/pgm')
sys.path.append('/home/mlapora/pgm/dash')
sys.path.append('/home/mlapora/pgm/dash/libs')
os.environ['DJANGO_SETTINGS_MODULE'] = 'dash.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
