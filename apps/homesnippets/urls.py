"""
Home snippets URL patterns
"""
from django.conf.urls.defaults import patterns, url

urlpatterns = patterns("homesnippets.views",

    # browser/components/nsBrowserContentHandler.js:911:    const SNIPPETS_URL = "http://snippets.mozilla.com/" + STARTPAGE_VERSION + "/%NAME%/%VERSION%/%APPBUILDID%/%BUILD_TARGET%/%LOCALE%/%CHANNEL%/%OS_VERSION%/%DISTRIBUTION%/%DISTRIBUTION_VERSION%/";
    url(r'^(?P<startpage_version>[^/]+)/(?P<name>[^/]+)/(?P<version>[^/]+)/(?P<appbuildid>[^/]+)/(?P<build_target>[^/]+)/(?P<locale>[^/]+)/(?P<channel>[^/]+)/(?P<os_version>[^/]+)/(?P<distribution>[^/]+)/(?P<distribution_version>[^/]+)/$',
        'view_snippets', name='view_snippets', kwargs={'preview': False}),

    url(r'^preview/(?P<startpage_version>[^/]+)/(?P<name>[^/]+)/(?P<version>[^/]+)/(?P<appbuildid>[^/]+)/(?P<build_target>[^/]+)/(?P<locale>[^/]+)/(?P<channel>[^/]+)/(?P<os_version>[^/]+)/(?P<distribution>[^/]+)/(?P<distribution_version>[^/]+)/$',
        'view_snippets', name='preview_snippets', kwargs={'preview': True}),

    url(r"^base64encode/(?P<url>.+)$", "base64_encode", name="base64_encode"),
    url(r"^admin/bulkDateChange$",
        "admin_bulk_date_change",
        name="admin_bulk_date_change"),
    url(r"^$", "index", name="index"),
)
