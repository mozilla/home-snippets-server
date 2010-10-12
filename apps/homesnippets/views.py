"""
Views for home snippets server
"""
from django.conf import settings

from django.core.urlresolvers import reverse

from django.http import HttpResponseRedirect, HttpResponse
from django.http import HttpResponseForbidden, HttpResponseNotModified

from django.template import RequestContext

from django.views.decorators import http
from django.views.decorators.vary import vary_on_headers
from django.views.decorators.cache import cache_control, cache_page

from django.shortcuts import render_to_response

from homesnippets.models import Snippet


HTTP_MAX_AGE = getattr(settings, 'SNIPPET_HTTP_MAX_AGE', 1)


@cache_page(HTTP_MAX_AGE, key_prefix='homesnippets')
@vary_on_headers('User-Agent', 'Cookie', 'Accept-Language')
@cache_control(public=True, max_age=HTTP_MAX_AGE)
def index(request):
    """Render the index page, simulating about:home"""
    return render_to_response('index.html', {},
            context_instance=RequestContext(request))


#TODO: Maybe use this? Figure out lighterweight way to work out ETag value from args
#def view_snippet_etag(request, **kwargs):
#    return '8675309'


@cache_page(HTTP_MAX_AGE, key_prefix='homesnippets')
@vary_on_headers('User-Agent', 'Cookie', 'Accept-Language')
@cache_control(public=True, max_age=HTTP_MAX_AGE)
#@http.condition(etag_func=view_snippet_etag)
def view_snippets(request, **kwargs):
    """Fetch and render snippets matching URL segment args"""
    # browser/components/nsBrowserContentHandler.js:911:    const SNIPPETS_URL = "http://snippets.mozilla.com/" + STARTPAGE_VERSION + "/%NAME%/%VERSION%/%APPBUILDID%/%BUILD_TARGET%/%LOCALE%/%CHANNEL%/%OS_VERSION%/%DISTRIBUTION%/%DISTRIBUTION_VERSION%/";

    snippets = Snippet.objects.all()

    out = [ ]
    for snippet in snippets:
        out.append('<div class="snippet">\n%s\n</div>' % snippet.body)

    resp = HttpResponse("\n\n".join(out))

    return resp

