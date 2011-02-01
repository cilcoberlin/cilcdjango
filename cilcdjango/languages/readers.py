
import codecs

class ISOLanguageTSVReader(object):
	"""A reader that interprets the ISO 639-3 tab-separated language list files."""

	_delimiter = u'\t'

	def __init__(self, tsv_file):
		"""Determine the file headers from the file instance `tsv_file`."""
		self._file = tsv_file
		self._headers = [
			header for header
			in self._file.readline().decode("utf-8").lstrip(unicode(codecs.BOM_UTF8, "utf-8")).rstrip('\n\r').split(self._delimiter)
		]

	@property
	def rows(self):
		"""Return each row in the TSV file as a dict keyed by the headers."""
		for row in self._file.readlines():
			cells = row.decode("utf-8").rstrip('\n\r').split(self._delimiter)
			yield dict(zip(self._headers, cells))
		self._file.close()
