
from cilcdjango.core.util import get_app_setting

from django import forms

import os
import re

#-------------------------------------------------------------------------------
#  Media Functions
#-------------------------------------------------------------------------------

def make_shared_media_url(path):
	"""
	Return the media path passed as `path` as an absolute URL rooted in the
	shared media folder.
	"""
	if not path.startswith("http"):
		path = os.path.join(get_app_setting('SHARED_MEDIA_URL'), path)
	return path

def make_secure_media_url(url):
	"""Return secure version of the given media URL."""
	return re.sub(r'^http:', 'https:', url)

#-------------------------------------------------------------------------------
#  Media Classes
#-------------------------------------------------------------------------------

class SharedMediaMixin(object):
	"""
	A mixin for any form, field or widget that defines a SharedMedia class whose
	values refer to media available as part of the cilcdjango library.

	The media specified in this special SharedMedia class will be merged into
	the media definition for the object using this mixin and available as
	absolute URLs.
	"""

	def _urls_for_media_list(self, file_list):
		"""
		Transform a list of media references into absolute URLs pointing to the
		shared media URL.
		"""

		new_files = []
		for file_path in file_list:
			new_files.append(make_shared_media_url(file_path))
		return tuple(new_files)

	def __getattribute__(self, attr):
		"""
		If the `media` attribute of the class using this mixin is being
		accessed, combine the shared media values with the media available
		through the class' Media class.
		"""

		value = super(SharedMediaMixin, self).__getattribute__(attr)

		#  If we are requesting media, merge our shared media files with the
		#  media base, then cache them for quicker access in the future
		if attr == 'media':
			if hasattr(self, '_shared_media'):
				return self._shared_media
			else:

				if hasattr(self, 'SharedMedia'):
					new_css = {}
					for media_type in getattr(self.SharedMedia, 'css', {}):
						new_css[media_type] = self._urls_for_media_list(self.SharedMedia.css[media_type])
					new_js = self._urls_for_media_list(getattr(self.SharedMedia, 'js', ()))
					new_media = forms.Media(css=new_css, js=new_js) + value

				else:
					new_media = value

				self._shared_media = new_media
				return new_media

		return value
