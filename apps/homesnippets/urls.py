"""
Home snippets URL patterns
"""
from django.conf.urls.defaults import patterns, url

urlpatterns = patterns("homesnippets.views",
    url(r'^(?P<startpage_version>[^/]+)/(?P<name>[^/]+)/(?P<version>[^/]+)/'
        '(?P<appbuildid>[^/]+)/(?P<build_target>[^/]+)/(?P<locale>[^/]+)/'
        '(?P<channel>[^/]+)/(?P<os_version>[^/]+)/(?P<distribution>[^/]+)/'
        '(?P<distribution_version>[^/]+)/$',
        'view_snippets', name='view_snippets', kwargs={'preview': False}),

    url(r'^preview/(?P<startpage_version>[^/]+)/(?P<name>[^/]+)/'
        '(?P<version>[^/]+)/(?P<appbuildid>[^/]+)/(?P<build_target>[^/]+)/'
        '(?P<locale>[^/]+)/(?P<channel>[^/]+)/(?P<os_version>[^/]+)/'
        '(?P<distribution>[^/]+)/(?P<distribution_version>[^/]+)/$',
        'view_snippets', name='preview_snippets', kwargs={'preview': True}),

    url(r'^base64encode$', 'base64_encode', name='base64_encode'),
    url(r'^admin/bulk_date_change$', 'admin_bulk_date_change',
        name='admin_bulk_date_change'),
    url(r'^show_all_snippets$', 'show_all_snippets', name='show_all_snippets'),
    url(r'^$', 'index', name='index'),
)
