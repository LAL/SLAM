import re
import itertools

from slam import interface

_HTML_TYPES = ('text/html', 'application/xhtml+xml')
_SUPPORTED_TRANSFORMS = ['PUT', 'DELETE']
_FORM_RE = re.compile(
    r'((<form\W[^>]*\bmethod=(\'|"|))(%s)((\'|"|)\b[^>]*>))'
    % '|'.join(_SUPPORTED_TRANSFORMS), re.IGNORECASE)
_MIDDLEWARE_KEY = 'method_middleware_transform'

class HttpMethodsMiddleware(object):
    """This middleware class allow web browser to perform PUT and DELETE
    requests by adding a hidden field to the forms.
    This middleware is *not* compatible with the Django's CSRF protection."""
    # Snippet from http://djangosnippets.org/snippets/174/

    def process_request(self, request):
        if request.POST and request.POST.has_key(_MIDDLEWARE_KEY):
            if request.POST[_MIDDLEWARE_KEY].upper() in _SUPPORTED_TRANSFORMS:
                request.method = request.POST[_MIDDLEWARE_KEY]
        return None

    def process_response(self, request, response):
        if response['Content-Type'].split(';')[0] in _HTML_TYPES:
            # ensure we don't add the 'id' attribute twice (HTML validity)
            idattributes = itertools.chain(("id='" + _MIDDLEWARE_KEY + "'",),
                                            itertools.repeat(''))
            def add_transform_field(match):
                """Returns the matched <form> tag with a modified method and
                the added <input> element"""
                return match.group(2) + "POST" + match.group(5) + \
                "<div style='display:none;'>" + \
                "<input type='hidden' " + idattributes.next() + \
                " name='" + _MIDDLEWARE_KEY + "' value='" + \
                match.group(4).upper() + "' /></div>"

            # Modify any POST forms
            response.content = _FORM_RE.sub(
                add_transform_field, response.content)
        return response


class LoginRecordMiddleware:
    """Record the login used inside slam.interface to correctly report it
    inside the logs."""

    def process_request(self, request):
        if request.user and request.user.username:
            interface.set_log_author(request.user.username)
        else:
            interface.set_log_author("rootEnDur")
        return None
