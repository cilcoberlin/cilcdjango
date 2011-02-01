
from cilcdjango.core.fields import RichTextEditorField
from cilcdjango.medialibrary.widgets import RichTextEditorWithMediaLibraryWidget

class RichTextEditorWithMediaLibraryField(RichTextEditorField):
	"""A rich text editor that can include media from a media library."""

	def __init__(self, library, *args, **kwargs):
		"""Receives a MediaLibrary instance as its first argument."""
		super(RichTextEditorWithMediaLibraryField, self).__init__(*args, **kwargs)
		self._library = library
		self.widget = RichTextEditorWithMediaLibraryWidget(library)
