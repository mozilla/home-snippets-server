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
DEBUG = getattr(settings, 'DEBUG', False)


@cache_page(HTTP_MAX_AGE, key_prefix='homesnippets')
@vary_on_headers('User-Agent', 'Cookie', 'Accept-Language')
@cache_control(public=True, max_age=HTTP_MAX_AGE)
def view_snippets(request, **kwargs):
    """Fetch and render snippets matching URL segment args"""
    # browser/components/nsBrowserContentHandler.js:911:    const SNIPPETS_URL = "http://snippets.mozilla.com/" + STARTPAGE_VERSION + "/%NAME%/%VERSION%/%APPBUILDID%/%BUILD_TARGET%/%LOCALE%/%CHANNEL%/%OS_VERSION%/%DISTRIBUTION%/%DISTRIBUTION_VERSION%/";

    snippets = Snippet.objects.all()

    out = [ ]
    for snippet in snippets:
        out.append('<div class="snippet">\n%s\n</div>' % snippet.body)

    if DEBUG:
        # HACK: This should probably be some sort of optional toolbar or
        # bookmarklet given to QA / devs
        from time import gmtime, strftime
        time_now = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
        out.append("""<div class="snippet">
            <hr /> 
            <p><a href="javascript:void(function%20()%20%7BlocalStorage%5B'snippets-last-update'%5D%20%3D%200%3B%20localStorage%5B'snippets'%5D%20%3D%20null%3B%20window.location.reload()%7D())">Click here to make about:home load fresh snippets</a></p>
            <p>Snippets last generated at: """ + time_now + """</p>
            <hr /> 
        </div>""")

    resp = HttpResponse("\n\n".join(out))
    resp['Access-Control-Allow-Origin'] = '*'
    return resp

@cache_page(HTTP_MAX_AGE, key_prefix='homesnippets')
@vary_on_headers('User-Agent', 'Cookie', 'Accept-Language')
@cache_control(public=True, max_age=HTTP_MAX_AGE)
def index(request):
    """Render the index page, simulating about:home"""
    return render_to_response('index.html', {},
            context_instance=RequestContext(request))
