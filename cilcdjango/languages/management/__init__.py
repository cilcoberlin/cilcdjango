
import cilcdjango.languages.models as languages_app

from django.db.models import get_models, signals

def populate_languages(app, created_models, verbosity, **kwargs):
	"""
	Populate the ISO languages table after the database has been synced, if the
	languages table has yet to be populated.
	"""

	from django.core.management import call_command
	from cilcdjango.languages.models import ISOLanguage

	if ISOLanguage in created_models:
		call_command("synclanguages")

signals.post_syncdb.connect(populate_languages,
	sender=languages_app, dispatch_uid="cilcdjango.languages.management.populate_languages")
