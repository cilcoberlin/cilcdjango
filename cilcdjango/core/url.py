
from cilcdjango.core.util import get_app_setting

from django.contrib.sites.models import Site
from django.http import HttpResponseRedirect

import urlparse

def make_url_absolute(url, secure=False):
	"""
	Return the absolute version of the either relative or absolute URL provided
	as `url`. If the optional `secure` parameter is True and the current site
	supports making HTTPS connections, a secure version of the URL will be
	returned.
	"""

	url = urlparse.urljoin("//%s" % Site.objects.get_current().domain, url)
	url_parts = list(urlparse.urlparse(url))
	url_parts[0] = "http%s" % ("s" * int(secure and get_app_setting('SUPPORTS_HTTPS')))

	return urlparse.urlunparse(url_parts)

def redirect_with_protocol(url, secure=False):
	"""
	Return an HTTP redirect response to the given URL, forcing the user to use a
	secure connection if `secure` is True and the current site supports secure
	connections.
	"""
	return HttpResponseRedirect(make_url_absolute(url, secure=secure))
