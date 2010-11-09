from django.conf import settings


class HttpOnlyMiddleware(object):
    """
    Set HttpOnly on all cookies except when specifically marked otherwise.

    Borrowed from:
    http://code.google.com/p/pageforest/source/browse/appengine/utils/cookies.py

    Compatible with Python 2.6+ only. Look at the URL for pre-2.6 support.
    """

    def process_response(self, request, response):
        for name in response.cookies:
            if name not in getattr(settings, 'JAVASCRIPT_READABLE_COOKIES', []):
                response.cookies[name]['httponly'] = "true"
        return response
