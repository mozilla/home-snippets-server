"""
Views for home snippets server
"""
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
DEBUG = getattr(settings, 'DEBUG', False)


#@cache_page(HTTP_MAX_AGE, key_prefix='homesnippets_view_snippets')
@cache_control(public=True, max_age=HTTP_MAX_AGE)
def view_snippets(request, **kwargs):
    """Fetch and render snippets matching URL segment args"""

    snippets = Snippet.objects.find_snippets_with_match_rules(kwargs)

    out = [ snippet['body'] for snippet in snippets ]

    out.append('<!-- content generated at %s -->' %
        strftime('%Y-%m-%dT%H:%M:%SZ', gmtime()))

    out_txt = '<div class="snippet_set">%s</div>' % "\n\n".join(out)

    resp = HttpResponse(out_txt)

    # TODO: bug 606555 - Get ACAO working with about:home?
    # resp['Access-Control-Allow-Origin'] = 'about:home' 
    # resp['Access-Control-Allow-Origin'] = 'about:home, http%s://%s' % ( 
    #     request.is_secure() and 's' or '', request.META['HTTP_HOST']) 
    resp['Access-Control-Allow-Origin'] = '*' 
    resp['Access-Control-Max-Age'] = HTTP_MAX_AGE
    resp['Access-Control-Allow-Methods'] = 'GET, HEAD, OPTIONS'

    return resp

@cache_control(public=True, max_age=HTTP_MAX_AGE)
def index(request):
    """Render the index page, simulating about:home"""
    return render_to_response('index.html', {},
            context_instance=RequestContext(request))
