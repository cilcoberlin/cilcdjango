
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.translation import ugettext_lazy as _

import cilcdjango.languages.models as language_models
import cilcdjango.languages.readers as readers

import os
import urllib2

DOWNLOAD_BASE   = "http://www.sil.org/iso639-3/"
CODE_SET_FILE   = "iso-639-3_20100707.tab"
NAME_INDEX_FILE = "iso-639-3_Name_Index_20100707.tab"

#  A map between the keys in the tab-separated ISO language list and the
#  attributes of the ISOLanguage model
ISO_LANGUAGE_LIST_MAP = {
	'Id':            'iso639_3',
	'Part2B':        'iso639_2_bibliographic',
	'Part2T':        'iso639_2_terminology',
	'Part1':         'iso639_1',
	'Scope':         'scope',
	'Language_Type': 'type',
	'Ref_Name':      'ref_name',
	'Comment':       'comment'
}

class Command(BaseCommand):

	help = _("creates a database of ISO 639-3 languages")

	def _get_remote_language_file(self, url):
		"""
		Return an instance of a file-like object representing the remote file
		named `url`.
		"""
		try:
			return urllib2.urlopen(os.path.join(DOWNLOAD_BASE, url))
		except urllib2.HTTPError:
			raise CommandError("Unable to download the language file %s" % url)

	@transaction.commit_manually
	def handle(self, *args, **kwargs):
		"""
		Updates the table containing a list of all available model extension plugins.
		"""

		ISOLanguage = language_models.ISOLanguage

		#  Read the language names index containing the print and inverted forms
		language_index = {}
		language_index_reader = readers.ISOLanguageTSVReader(self._get_remote_language_file(NAME_INDEX_FILE))
		for index in language_index_reader.rows:
			language_index[index['Id']] = {
				'inverted': index['Inverted_Name'],
				'print':    index['Print_Name']
			}

		#  Read in the list of all ISO 639-3 language, updating any existing
		#  languages, adding non-present ones, and cross-referencing with the
		#  language names index to get the proper printed and inverted name
		#  forms of the language
		language_list_reader = readers.ISOLanguageTSVReader(self._get_remote_language_file(CODE_SET_FILE))
		for counter, language in enumerate(language_list_reader.rows):
			try:
				iso_language = ISOLanguage.objects.get(iso639_3=language['Id'])
			except ISOLanguage.DoesNotExist:
				iso_language = ISOLanguage()
			for file_key, model_key in ISO_LANGUAGE_LIST_MAP.iteritems():
				setattr(iso_language, model_key, language.get(file_key, u"") or None)
			index = language_index[language['Id']]
			iso_language.print_name = index['print']
			iso_language.inverted_name = index['inverted']
			iso_language.save()
			print "Adding language %(id)s" % {'id': language['Id']}

		print "Saving languages to database..."
		transaction.commit()
		print "All ISO 639 languages added"
