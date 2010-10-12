from django.conf import settings
from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
    (r'^', include('homesnippets.urls')),
)

if settings.SERVE_MEDIA:
    urlpatterns += patterns("",
        (r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}),
    )
