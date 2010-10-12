"""
Views for home snippets server
"""
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.http import HttpResponseForbidden
from django.template import RequestContext
from homesnippets.models import Snippet


def view_snippet(request, **kwargs):
    # browser/components/nsBrowserContentHandler.js:911:    const SNIPPETS_URL = "http://snippets.mozilla.com/" + STARTPAGE_VERSION + "/%NAME%/%VERSION%/%APPBUILDID%/%BUILD_TARGET%/%LOCALE%/%CHANNEL%/%OS_VERSION%/%DISTRIBUTION%/%DISTRIBUTION_VERSION%/";
    snippets = Snippet.objects.all()

    out = []
    for snippet in snippets:
        out.append('<div class="snippet">%s</div>' % snippet.body)
    return HttpResponse("\n\n".join(out))

