"""
Home snippets URL patterns
"""
from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

urlpatterns = patterns("homesnippets.views",

    # browser/components/nsBrowserContentHandler.js:911:    const SNIPPETS_URL = "http://snippets.mozilla.com/" + STARTPAGE_VERSION + "/%NAME%/%VERSION%/%APPBUILDID%/%BUILD_TARGET%/%LOCALE%/%CHANNEL%/%OS_VERSION%/%DISTRIBUTION%/%DISTRIBUTION_VERSION%/";
    url(r'^(?P<STARTPAGE_VERSION>[^/]+)/(?P<NAME>[^/]+)/(?P<VERSION>[^/]+)/(?P<APPBUILDID>[^/]+)/(?P<BUILD_TARGET>[^/]+)/(?P<LOCALE>[^/]+)/(?P<CHANNEL>[^/]+)/(?P<OS_VERSION>[^/]+)/(?P<DISTRIBUTION>[^/]+)/(?P<DISTRIBUTION_VERSION>[^/]+)/$', 
        'view_snippet', name='view_snippets'),

    url(r"^$", "index", name="index"),
)
