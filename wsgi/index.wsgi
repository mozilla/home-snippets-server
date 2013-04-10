import os
import site
import sys
from datetime import datetime

try:
    import newrelic.agent
except ImportError:
    newrelic = False


# If New Relic was imported successfully, load the configuration.
if newrelic:
    newrelic_ini = os.getenv('NEWRELIC_PYTHON_INI_FILE', False)
    if newrelic_ini:
        newrelic.agent.initialize(newrelic_ini)
    else:
        newrelic = False

# fix markdown.py (and potentially others) using stdout
sys.stdout = sys.stderr

# Remember when mod_wsgi loaded this file so we can track it in nagios.
wsgi_loaded = datetime.now()

# Add the main dir to the python path so we can import manage.
wsgidir = os.path.dirname(__file__)
site.addsitedir(os.path.abspath(os.path.join(wsgidir, '../')))

# manage adds /apps, /lib, and /vendor to the Python path.
import manage

import django.conf
import django.core.handlers.wsgi
import django.core.management
import django.utils

# Do validate and activate translations like using `./manage.py runserver`.
# http://blog.dscpl.com.au/2010/03/improved-wsgi-script-for-use-with.html
utility = django.core.management.ManagementUtility()
command = utility.fetch_command('runserver')
command.validate()

# This is what mod_wsgi runs.
django_app = django.core.handlers.wsgi.WSGIHandler()


def application(env, start_response):
    env['wsgi.loaded'] = wsgi_loaded
    return django_app(env, start_response)

# Wrap the WSGI application with New Relic if we're able to.
if newrelic:
    application = newrelic.agent.wsgi_application()(application)
