
from cilcdjango.core.markup import embed_flash
from cilcdjango.medialibrary.renderers.base import RendererType
import cilcdjango.medialibrary.settings as _settings

from django.template.defaultfilters import slugify

import os

def file_renderer_factory(mime_type):
	"""
	Return the renderer class that can render a file with the MIME type given in
	the string `mime_type`.

	If no appropriate renderer can be found for the specific MIME type, the
	basic file renderer, which returns a link to the media, will be used.
	"""
	for renderer in BaseFileRenderer.renderers:
		if mime_type in renderer.mime_types:
			return renderer
	return BaseFileRenderer

class FileRendererType(RendererType):
	"""Metaclass for any file renderer."""
	pass

class BaseFileRenderer(object):
	"""
	Base class for all file renderers.

	Child classes can and should specify a `formats` attribute, which is an
	iterable of MIME type strings that the renderer should be used to display.
	"""

	__metaclass__ = FileRendererType

	mime_types = []

	def render(self, medium):
		"""Render the MediaItem instance `medium` as a download link."""
		return u"<a href=\"%(url)s\" rel=\"uploaded-file\" class=\"media media-%(media)s\">%(title)s</a>" % {
			'url':   medium.file.url,
			'title': medium.title,
			'media': slugify(medium.type.name)
		}

class ImageRenderer(BaseFileRenderer):
	"""A renderer that displays an image as an <img> tag."""

	mime_types = [
		'image/jpeg',
		'image/gif',
		'image/png'
	]

	def render(self, medium):
		"""Render the medium as an embedded image."""
		return u"<img src=\"%(src)s\" alt=\"%(alt)s\" />" % {
			'src': medium.file.url,
			'alt': medium.title
		}

class EmbeddedMediaRenderer(BaseFileRenderer):
	"""
	Base class for an embedded audio or video file that displays the file in a
	Flash player.

	Child classes must define a `player_height` and `player_width` attribute,
	which will be ints that define the dimensions of the embedded Flash player.
	"""

	def render(self, medium):
		"""Embed the media in a Flash player."""

		player_id = "media-player-%d" % medium.pk
		flashvars = {
			'file': medium.file.url,
			'id': player_id
		}
		flashvars.update(self.add_flashvars())

		return embed_flash(
			os.path.join(_settings.MEDIA_URL, _settings.MEDIA_PLAYER_URL),
			player_id,
			self.player_width,
			self.player_height,
			flashvars=flashvars
		)

	def add_flashvars(self):
		"""Allow a child renderer to add flashvars to the embed code."""
		return {}

class AudioRenderer(EmbeddedMediaRenderer):
	"""Renders the audio using an embedded Flash player."""

	player_width  = 300
	player_height = 24

	mime_types = [
		'audio/mpeg'
	]

class VideoRenderer(EmbeddedMediaRenderer):
	"""Renders the audio using an embedded Flash player."""

	player_width  = 328
	player_height = 200

	mime_types = [
		'video/mpeg',
		'video/quicktime',
		'video/mp4'
	]
