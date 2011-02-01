
from cilcdjango.core.markup import embed_flash
from cilcdjango.medialibrary.renderers.base import RendererType

from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _

import cgi
import urllib
import urlparse
try:
	from urlparse import parse_qs
except ImportError:
	from cgi import parse_qs

def url_renderer_factory(site):
	"""
	Return the renderer class capable of rendering the file at the URL passed in
	`site`.

	If no appropriate renderer is found, the default URL is used, which returns
	a link to the URL.
	"""
	for renderer in BaseURLRenderer.renderers:
		if site in renderer.sites:
			return renderer
	return BaseURLRenderer

class URLRendererType(RendererType):
	"""Metaclass for any URL renderer."""
	pass

class BaseURLRenderer(object):
	"""
	Base class for any URL renderers.

	Child classes can and should defined a `sites` attribute that is an iterable
	containing the domains that it can render.
	"""

	__metaclass__ = URLRendererType

	sites = []

	def render(self, medium):
		"""Returns a link to the remote MediaItem instance `medium`."""
		return u"<a href=\"%(url)s\" rel=\"library-url\" class=\"site-%(media)s\" title=\"%(alt)s\">%(title)s</a>" % {
			'url': medium.url,
			'title': medium.title,
			'alt': _("view link on %(site)s") % {'site': medium.type.name},
			'media': slugify(medium.type.name)
		}

class YouTubeRenderer(BaseURLRenderer):
	"""
	A renderer that displays a YouTube video, identified by the URL of the
	containing page, using the YouTube Flash player.
	"""

	_DEFAULT_HEIGHT  = 340
	_DEFAULT_WIDTH   = 560
	_VIDEO_QUERY_KEY = "v"
	_VIDEO_URL_BASE  = "http://www.youtube.com/v/"

	sites = [
		'www.youtube.com'
	]

	def render(self, medium):
		"""
		Return markup to embed the YouTube video in the page using YouTube's
		Flash player.
		"""

		#  Build the video embed code by getting the video ID from the URL
		url_parts = urlparse.urlparse(medium.url)
		query_parts = parse_qs(url_parts.query)
		video_id = query_parts.get(self._VIDEO_QUERY_KEY, [''])[0]
		video_url = "%(base)s%(id)s?%(query)s" % {
			'base': self._VIDEO_URL_BASE,
			'id': video_id,
			'query': cgi.escape(urllib.urlencode({
				'fs': 1,
				'hl': 'en_US',
				'rel': 0
			}))
		}

		return embed_flash(
			video_url,
			video_id,
			self._DEFAULT_WIDTH,
			self._DEFAULT_HEIGHT
		)
