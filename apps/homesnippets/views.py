"""
Views for home snippets server
"""
import random
import base64
from time import time, mktime, gmtime, strftime
from urllib2 import urlopen, URLError

from django.conf import settings

from django.core.urlresolvers import reverse

from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.http import HttpResponseForbidden, HttpResponseNotModified

from django.utils import simplejson

from django.contrib.admin.views.decorators import staff_member_required

from django.template import RequestContext

from django.views.decorators import http
from django.views.decorators.vary import vary_on_headers
from django.views.decorators.cache import cache_control, cache_page

from django.shortcuts import render_to_response

from homesnippets.models import Snippet


HTTP_MAX_AGE = getattr(settings, 'SNIPPET_HTTP_MAX_AGE', 1)
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

    preview = kwargs['preview']
    snippets = Snippet.objects.find_snippets_with_match_rules(kwargs)

    if len(snippets) == 0:
        out_txt = ''
    else:
        out = [ snippet['body'] for snippet in snippets ]

        out.append('<!-- content generated at %s -->' %
            ( strftime('%Y-%m-%dT%H:%M:%SZ', gmtime() ) ) )

        out_txt = '<div class="snippet_set">%s</div>' % "\n\n".join(out)

    resp = HttpResponse(out_txt)

    if preview:
        # Try to force preview request to be fresh.
        max_age = 0
        resp['Cache-Control'] = 'public, must-revalidate, max-age=0'
    else:
        max_age = HTTP_MAX_AGE
        resp['Cache-Control'] = 'public, max-age=%s' % ( HTTP_MAX_AGE )

    # TODO: bug 606555 - Get ACAO working with about:home?
    resp['Access-Control-Allow-Origin'] = '*' 
    resp['Access-Control-Max-Age'] = max_age
    resp['Access-Control-Allow-Methods'] = 'GET, HEAD, OPTIONS'

    resp['X-FRAME-OPTIONS'] = None

    return resp

@staff_member_required
def base64_encode(request, **kwargs):
    """Encode a remote image to base64, and output as JSON"""

    url = kwargs['url']
    try:
        img_file = urlopen(url)
        base64_str = base64.encodestring(img_file.read())
    except (URLError, ValueError):
        raise Http404
        
    return HttpResponse(simplejson.dumps({'img': base64_str}),
                        mimetype='applications/json')
