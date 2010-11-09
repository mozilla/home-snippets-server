"""
Useful middleware for the home snippets app
"""
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

class XFrameOptionsMiddleware(object):
    """Append an X-Frame-Options output header to responses."""
    def process_response(self, request, response):
        """Append an X-Frame-Options output header to responses."""
        if not 'X-FRAME-OPTIONS' in response:
            options = getattr(settings, 'X_FRAME_OPTIONS', 'DENY')
            # If no header set already, set one from settings
            response['X-FRAME-OPTIONS'] = options.upper()
        elif 'None' == response['X-FRAME-OPTIONS']:
            # If there is a header, but it's false, just delete it
            # Kind of a hack, because setting to None gets stringified to 'None'
            del response['X-FRAME-OPTIONS']
        return response
