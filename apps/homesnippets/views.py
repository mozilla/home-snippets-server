"""
Views for home snippets server
"""
import base64
import json
from time import gmtime, strftime
from urllib2 import urlopen, URLError

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.cache import cache_control

from homesnippets.forms import BulkDateForm
from homesnippets.models import Snippet


HTTP_MAX_AGE = getattr(settings, 'SNIPPET_HTTP_MAX_AGE', 1)
DEBUG = getattr(settings, 'DEBUG', False)


@cache_control(public=True, max_age=HTTP_MAX_AGE)
def index(request):
    """Render the index page, simulating about:home."""
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
    """Fetch and render snippets matching URL segment args."""

    preview = kwargs['preview']
    snippets = Snippet.objects.find_snippets_with_match_rules(kwargs)

    if len(snippets) == 0:
        out_txt = ''
    else:
        out = []
        for snippet in snippets:
            attrs = {'data-snippet-id': snippet['id']}
            if snippet['country']:
                attrs['data-country'] = snippet['country']

            attrs_string = ' '.join(['%s="%s"' % (key, value) for key, value in
                                     attrs.items()])
            out.append('<div %s>%s</div>' % (attrs_string, snippet['body']))

        out.append('<!-- content generated at %s -->' %
            (strftime('%Y-%m-%dT%H:%M:%SZ', gmtime())))

        out_txt = '<div class="snippet_set">%s</div>' % "\n\n".join(out)

    resp = HttpResponse(out_txt)

    if preview:
        # Try to force preview request to be fresh.
        max_age = 0
        resp['Cache-Control'] = 'public, must-revalidate, max-age=0'
    else:
        max_age = HTTP_MAX_AGE
        resp['Cache-Control'] = 'public, max-age=%s' % (HTTP_MAX_AGE)

    # TODO: bug 606555 - Get ACAO working with about:home?
    resp['Access-Control-Allow-Origin'] = '*'
    resp['Access-Control-Max-Age'] = max_age
    resp['Access-Control-Allow-Methods'] = 'GET, HEAD, OPTIONS'

    resp['X-FRAME-OPTIONS'] = None

    return resp


@staff_member_required
def base64_encode(request, **kwargs):
    """Encode a remote image to base64, and output as JSON."""

    try:
        url = request.GET['url']
        img_file = urlopen(url)
        base64_str = base64.encodestring(img_file.read())
    except (URLError, ValueError, KeyError):
        raise Http404

    return HttpResponse(json.dumps({'img': base64_str}),
                        mimetype='applications/json')


@staff_member_required
def admin_bulk_date_change(request, **kwargs):
    """Show a custom form to bulk-change snippet start and end dates."""

    if request.method == 'POST':
        form = BulkDateForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']

            snippet_ids = form.cleaned_data['ids'].split(',')
            snippets = Snippet.objects.filter(id__in=snippet_ids)
            snippets.update(pub_start=start_date, pub_end=end_date)

            return HttpResponseRedirect('/admin/homesnippets/snippet/')
    else:
        form = BulkDateForm(initial=request.GET)

    return render_to_response('adminBulkDateChange.html',
                              {'form': form},
                              context_instance=RequestContext(request))


@cache_control(public=True, max_age=3600)
def show_all_snippets(request):
    """
    Show a list of all public snippets and their relevant client match rules.
    """
    snippets = Snippet.objects.filter(disabled=False, preview=False)
    fields = ('startpage_version', 'name', 'version', 'appbuildid',
              'build_target', 'locale', 'channel', 'os_version',
              'distribution', 'distribution_version')
    return render_to_response('show_all_snippets.html',
                              {'snippets': snippets, 'fields': fields},
                              context_instance=RequestContext(request))
