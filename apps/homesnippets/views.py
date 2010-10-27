"""
Views for home snippets server
"""
import random
from time import time, mktime, gmtime, strftime

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
HTTP_MAX_AGE_FUZZ = getattr(settings, 'SNIPPET_HTTP_MAX_AGE_FUZZ', 0.1)
DEBUG = getattr(settings, 'DEBUG', False)


@cache_control(public=True, max_age=HTTP_MAX_AGE)
def index(request):
    """Render the index page, simulating about:home"""
    return render_to_response('index.html', {},
            context_instance=RequestContext(request))

@cache_control(public=True, max_age=HTTP_MAX_AGE)
def handler404(request):
    """For 404's, just return a blank cacheable 200 OK response.

    This is a hack, but it keeps 404 traffic from falling through to the origin
    server as much.
    """
    resp = HttpResponse('')
    resp['Access-Control-Allow-Origin'] = '*' 
    resp['Access-Control-Max-Age'] = HTTP_MAX_AGE
    resp['Access-Control-Allow-Methods'] = 'GET, HEAD, OPTIONS'
    return resp

def view_snippets(request, **kwargs):
    """Fetch and render snippets matching URL segment args"""

    snippets = Snippet.objects.find_snippets_with_match_rules(kwargs)

    out = [ snippet['body'] for snippet in snippets ]

    out.append('<!-- content generated at %s -->' %
        strftime('%Y-%m-%dT%H:%M:%SZ', gmtime()))

    out_txt = '<div class="snippet_set">%s</div>' % "\n\n".join(out)

    resp = HttpResponse(out_txt)

    # HACK: Produce a max-age for the cache with a fuzz factor, so as to
    # help spread out any thundering herds on frontend cache expiry
    fuzz = int(HTTP_MAX_AGE * HTTP_MAX_AGE_FUZZ)
    max_age = HTTP_MAX_AGE + random.randint(-fuzz, fuzz)
    resp['Cache-Control'] = 'public, max-age=%s' % ( max_age )

    # TODO: bug 606555 - Get ACAO working with about:home?
    resp['Access-Control-Allow-Origin'] = '*' 
    resp['Access-Control-Max-Age'] = max_age
    resp['Access-Control-Allow-Methods'] = 'GET, HEAD, OPTIONS'

    return resp

