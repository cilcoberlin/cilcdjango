
from cilcdjango.core.media import SharedMediaMixin
from cilcdjango.medialibrary.forms import MediaLibraryForm
from cilcdjango.core.widgets import RichTextEditorWidget

from django.template.loader import render_to_string

class RichTextEditorWithMediaLibraryWidget(RichTextEditorWidget, SharedMediaMixin):
	"""A widget that renders a rich text editor and media library selection fields."""

	def __init__(self, library, *args, **kwargs):
		"""Requires a MediaLibrary instance as its first argument."""

		#  Add in the JavaScript glue code to bridge the library and the editor
		try:
			self.SharedMedia.js = self.SharedMedia.js + ('medialibrary/js/editor.js',)
		except AttributeError:
			pass

		self._library = library
		super(RichTextEditorWithMediaLibraryWidget, self).__init__(*args, **kwargs)

	def render(self, name, value, attrs=None):
		"""Add the media library markup after the RTE markup."""

		try:
			editor_id = attrs.get('id', None)
		except AttributeError:
			editor_id = None

		return "%s%s" % (
			super(RichTextEditorWithMediaLibraryWidget, self).render(name, value, attrs),
			render_to_string('media_forms/editor_form.html', {
				'editor_id': editor_id,
				'form': MediaLibraryForm(self._library),
				'library': self._library
			})
		)
