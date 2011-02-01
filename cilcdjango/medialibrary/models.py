
from cilcdjango.medialibrary import renderers
import cilcdjango.medialibrary.settings as _settings
from cilcdjango.core.text import smart_title

from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

import mimetypes
import os
import re
from urlparse import urlparse

#-------------------------------------------------------------------------------
#  Media Library
#-------------------------------------------------------------------------------

class MediaLibraryManager(models.Manager):
	"""Custom manager for the MediaLibrary model."""
	pass

class MediaLibrary(models.Model):
	"""
	A media library that aggregates local and remote media.

	This library will generally be subclassed by an application that requires
	media library functionality, adding information to only allow access to a
	media library to certain objects, for example.
	"""

	objects = MediaLibraryManager()

	class Meta:
		verbose_name = _("media library")
		verbose_name_plural = _("media libraries")

	def all_media_types(self, local=None, media=None):
		"""
		Return an alphabetically sorted list of all media subtypes that appear
		in the current media library for the given media type grouping.
		"""

		#  Use a passed media set or the default of all media for the library
		if media is not None:
			media_set = media
		else:
			media_set = self.media

		#  Create a list of types, keeping track of the added names to avoid
		#  having duplicate display names
		used_types = []
		if local is None:
			base_types = MediaType.objects.all()
		else:
			base_types = MediaType.objects.filter(local=local)
		for media_type in base_types:
			if media_type.name in used_types or not media_set.filter(type=media_type).count():
				base_types = base_types.exclude(pk=media_type.pk)
			used_types.append(media_type.name)
		return base_types.order_by('name')

	def filter_media(self, local=None, media_type=None, group=None):
		"""
		Return the media types and actual media items available for the given
		filters.

		The `local` kwarg is a Boolean specifying whether or not the medium is a
		local file or a remote URL, `media_type` is a MediaType instance, and
		`group` is a MediaLibraryGroup instance.
		"""

		media = Q()

		#  Filter by group, and get the available types for the group
		if group:
			media &= Q(groups=group)
		types = self.all_media_types(local=local, media=MediaItem.objects.filter(media))

		#  Filter by the local or remote media type
		if local is not None:
			media &= Q(type__local=local)
		if media_type:
			media &= Q(type__name=media_type)

		return {
			'types': types,
			'media': MediaItem.objects.filter(media).order_by('title')
		}

class MediaLibraryGroup(models.Model):
	"""A grouping that can be applied to a MediaItem instance."""

	name    = models.CharField(max_length=255, verbose_name=_("group name"))
	library = models.ForeignKey(MediaLibrary, verbose_name=_("media library"), related_name="groups")
	media   = models.ManyToManyField('MediaItem', verbose_name=_("media items"), related_name="groups")

	class Meta:
		verbose_name = _("media group")
		verbose_name_plural = _("media groups")

	def __unicode__(self):
		return self.name

class MediaTypeManager(models.Manager):
	"""Custom manager for the MediaType model."""

	#  If the MIME type begins with one of these, use this as the display name
	_MIME_TYPE_PREFIX_GROUPS = (
		'audio',
		'image',
		'video'
	)

	#  Mapping of common extensions not frequently found by mimetypes
	_NONSTANDARD_EXTENSIONS = {
		'docx': "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
		'pptx': "application/vnd.openxmlformats-officedocument.presentationml.presentation",
		'xlsx': "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
	}

	#  Manual overrides for the display name of certain MIME types
	_NAME_OVERRIDES = {
		"application/octet-stream": "unknown",
		"application/msword": "MS Word",
		"application/vnd.openxmlformats-officedocument.wordprocessingml.document": "MS Word",
		"application/vnd.ms-excel": "MS Excel",
		"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "MS Excel",
		"application/vnd.ms-powerpoint": "MS PowerPoint",
		"application/vnd.openxmlformats-officedocument.presentationml.presentation": "MS PowerPoint",
	}

	_DEFAULT_MIME_TYPE = "application/octet-stream"

	def get_or_create_for_file(self, filename):
		"""
		Get or create a MediaType based on the MIME type of the file, whose name
		is passed in the string `filename`.
		"""

		mimetypes.init()
		mime_type, encoding = mimetypes.guess_type(filename)
		if not mime_type:
			mime_type = self._NONSTANDARD_EXTENSIONS.get(os.path.splitext(filename)[1].lstrip("."), self._DEFAULT_MIME_TYPE)

		#  If there is no database entry for the MIME type, take an educated
		#  guess at how to build the display name for the media type, using the
		#  media's MIME type, unless a name exists for it in the lookup table
		type_args = {
			'type': mime_type,
			'local': True
		}
		try:
			media_type = MediaType.objects.get(**type_args)
		except MediaType.DoesNotExist:
			if mime_type in self._NAME_OVERRIDES:
				media_name = self._NAME_OVERRIDES[mime_type]
			else:
				prefix, suffix = mime_type.split("/")
				if prefix in self._MIME_TYPE_PREFIX_GROUPS:
					media_name = prefix
				else:
					media_name = re.sub(r'^vnd\.|x-', '', suffix)
					media_name = re.sub(r'[-\.\_]', ' ', media_name)
				if len(media_name) <= 4 and not media_name.count(" "):
					media_name = media_name.upper()
				else:
					media_name = smart_title(media_name)
			media_type = MediaType(name=media_name, **type_args)
			media_type.save()

		return media_type

	def get_or_create_for_url(self, url):
		"""Get or create a MediaType based on the base site of the URL."""

		parsed_url = urlparse(url)
		site = parsed_url.netloc

		#  If the URL has yet to be added, create a new type record for the
		#  site, with the type as the network location and the name as a guess
		#  from the path stripped of the subdomain and TLD indicators
		type_args = {
			'type': site,
			'local': False
		}
		try:
			media_type = MediaType.objects.get(**type_args)
		except MediaType.DoesNotExist:
			site_parts = site.split(".")
			try:
				site_name = site_parts[1].title()
			except IndexError:
				site_name = site
			media_type = MediaType(name=site_name, **type_args)
			media_type.save()

		return media_type

class MediaType(models.Model):
	"""A type of media file, which can be applied either to a URL or a file."""

	objects = MediaTypeManager()

	name  = models.CharField(max_length=255, verbose_name=_("display name"))
	type  = models.CharField(max_length=255, verbose_name=_("type identifier"))
	local = models.BooleanField(default=True, verbose_name=_("is a local file"))

	class Meta:
		verbose_name = _("media type")
		verbose_name_plural = _("media types")

	def __unicode__(self):
		return self.name

def set_media_item_upload_path(instance, filename):
	"""
	Set the path for uploaded media files to a directory keyed by the ID of the
	MediaLibrary associated with the MediaItem instance.
	"""
	return os.path.join(_settings.UPLOADED_FILES_DIRECTORY, "%04d" % instance.library.pk, filename)

class MediaItem(models.Model):
	"""An individual media file."""

	file    = models.FileField(upload_to=set_media_item_upload_path, verbose_name=_("media file"), null=True, blank=True)
	url     = models.URLField(verbose_name=_("external media URL"), null=True, blank=True)
	title   = models.CharField(max_length=200, verbose_name=_("title"))
	library = models.ForeignKey(MediaLibrary, verbose_name=("media library"), related_name="media")
	type    = models.ForeignKey(MediaType, verbose_name=_("medium type"), related_name="media")

	class Meta:
		verbose_name = _("media file")
		verbose_name_plural = _("media files")

	def __unicode__(self):
		return self.title

	def save(self, *args, **kwargs):
		"""Link the media file to a type before saving it."""

		#  Link the file to a MediaType, creating one if it doesn't exist
		if self.file:
			media_type = MediaType.objects.get_or_create_for_file(self.file.name)
		if self.url:
			media_type = MediaType.objects.get_or_create_for_url(self.url)
		self.type = media_type

		super(MediaItem, self).save(*args, **kwargs)

	def get_renderer(self):
		"""Return an instance of the renderer used to display the file."""

		#  Try to generate a renderer class from a factory
		media_type = self.type.type
		if self.file:
			render_class = renderers.files.file_renderer_factory(media_type)
		elif self.url:
			render_class = renderers.urls.url_renderer_factory(media_type)

		#  If a renderer class was made, return a renderer instance
		if render_class:
			return render_class()
		else:
			return None

	def render(self):
		"""
		Return the markup required to render the file in a page, using the
		renderer specified for the type of file in the media library.

		For some files, such as images, this might return code that directly
		embeds the image in the document. For others, such as PDF files, it will
		simply return a link to download the file.
		"""
		try:
			return self.get_renderer().render(self)
		except AttributeError:
			return _("no appropriate renderer for the file could be found ")
