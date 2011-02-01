
from cilcdjango.core.util import get_app_setting

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

import os
import re

def make_url_list_absolute(url_list, url_prefix):
	"""
	Transform a list of relative urls contained in `url_list` into absolute ones
	rooted in `url_prefix`.
	"""
	absolute_urls = []
	for url in url_list:
		if not url.startswith('http'):
			url = os.path.join(url_prefix, url)
		absolute_urls.append(url)
	return absolute_urls

def reverse_absolute(view_name, args=[], kwargs={}, secure=False):
	"""
	Return the absolute URL for the relative URL provided by a call to the view
	named `view_name` with the given view args and kwargs.

	If `secure` is True and the current site supports HTTPS, a secure absolute
	URL will be returned.
	"""
	return os.path.join(
		site_url(secure),
		fix_url(reverse(view_name, args=args, kwargs=kwargs)).lstrip("/"))

def site_url(secure=False):
	"""
	Return the base URL of the current site, return a secure HTTPS URL if
	`secure` is True and the current site supports secure connection, and
	otherwise returning a standard HTTP connection with an optional non-standard
	port.
	"""
	make_secure = secure and get_app_setting('SUPPORTS_HTTPS')
	base_port = get_app_setting('SERVER_PORT')
	site_base = "http%s://%s" % ( "s" * int(make_secure), get_app_setting('SERVER_BASE') )
	return "%s%s" % (site_base, ":%s" % base_port * int(base_port != 80 and not make_secure))

def fix_url(current_url):
	"""
	Return the given URL, with the base folder for the current site prepended to
	it if the site is not running from the server root.
	"""
	root_folder = get_app_setting('APP_ROOT_FOLDER')
	url_parts = [current_url]
	if not current_url.startswith(root_folder):
		url_parts.insert(0, root_folder.rstrip("/"))
	return "".join(url_parts)

def normalize_url(current_url):
	"""Return the current URL with the site root folder removed from the start."""
	return re.sub(r'^%s' % get_app_setting('APP_ROOT_FOLDER').rstrip("/"), '', current_url)

def redirect_with_protocol(url, secure=False):
	"""
	Return an HTTP redirect response to the given URL, forcing the user to use a
	secure connection if `secure` is True and the current site supports secure
	connections.
	"""
	return HttpResponseRedirect(os.path.join(site_url(secure), fix_url(url).lstrip("/")))
