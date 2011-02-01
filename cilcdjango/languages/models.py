
from django.db import models
from django.utils.translation import ugettext_lazy as _

from cilcdjango.core.models import AutoSlugField

#  ISO language scopes
ISO_SCOPE_INDIVIDUAL    = 'I'
ISO_SCOPE_MACROLANGUAGE = 'M'
ISO_SCOPE_SPECIAL       = 'S'

ISO_SCOPE_CHOICES = (
	(ISO_SCOPE_INDIVIDUAL, _("individual")),
	(ISO_SCOPE_MACROLANGUAGE, _("macrolanguage")),
	(ISO_SCOPE_SPECIAL, _("special"))
)

#  ISO language types
ISO_TYPE_ANCIENT     = 'A'
ISO_TYPE_CONSTRUCTED = 'C'
ISO_TYPE_EXTINCT     = 'E'
ISO_TYPE_HISTORICAL  = 'H'
ISO_TYPE_LIVING      = 'L'
ISO_TYPE_SPECIAL     = 'S'

ISO_TYPE_CHOICES = (
	(ISO_TYPE_ANCIENT, _("ancient")),
	(ISO_TYPE_CONSTRUCTED, _("constructed")),
	(ISO_TYPE_EXTINCT, _("extinct")),
	(ISO_TYPE_HISTORICAL, _("historical")),
	(ISO_TYPE_LIVING, _("living")),
	(ISO_TYPE_SPECIAL, _("special")),
)

class ISOLanguageManager(models.Manager):
	"""Custom manager for the ISOLanguage model."""

	def iso639_1(self):
		"""
		Return a queryset of all languages covered by the ISO 639-1 standard,
		sorted by their reference name.
		"""
		return self.filter(iso639_1__isnull=False).order_by('ref_name')

	def iso639_2(self):
		"""
		Return a queryset of all languages covered by the ISO 639-2 standard,
		sorted by their reference name.
		"""
		return self.filter(
			iso639_2_bibliographic__isnull=False,
			iso639_2_terminology__isnull=False).order_by('ref_name')

	def iso639_3(self):
		"""
		Return a queryset of all languages covered by the ISO 639-3 standard,
		sorted by their reference name.
		"""
		return self.filter(iso639_3__isnull=False).order_by('ref_name')

	def basic(self):
		"""
		Return a queryset of any living languages covered by ISO 639-1, sorted
		by their reference name.
		"""
		return self.filter(iso639_1__isnull=False, type=ISO_TYPE_LIVING).order_by('ref_name')

	def alphabetical(self):
		"""
		Return a queryset of all the languages sorted by their reference name,
		sorted by their reference name.
		"""
		return self.order_by('ref_name')

class ISOLanguage(models.Model):
	"""A language covered by the ISO 639 standard."""

	objects                = ISOLanguageManager()

	iso639_3               = models.CharField(max_length=3, verbose_name=_("ISO 639-3 identifier"))
	iso639_2_bibliographic = models.CharField(max_length=3, verbose_name=_("ISO 639-2 bibliographic identifier"), null=True)
	iso639_2_terminology   = models.CharField(max_length=3, verbose_name=_("ISO 639-2 terminology identifier"), null=True)
	iso639_1               = models.CharField(max_length=2, verbose_name=_("ISO 639-1 identifier"), null=True)

	scope                  = models.CharField(max_length=1, verbose_name=_("language scope"), choices=ISO_SCOPE_CHOICES)
	type                   = models.CharField(max_length=1, verbose_name=_("language type"), choices=ISO_TYPE_CHOICES)

	ref_name               = models.CharField(max_length=150, verbose_name=_("reference name"))
	ref_name_slug          = AutoSlugField(max_length=150, verbose_name=_("reference name slug"), populate_from="ref_name")
	print_name             = models.CharField(max_length=75, verbose_name=_("print name"))
	inverted_name          = models.CharField(max_length=75, verbose_name=_("inverted name"))
	comment                = models.CharField(max_length=150, verbose_name=_("comment"), null=True)

	class Meta:
		verbose_name = _("ISO 639-3 language")
		verbose_name_plural = _("ISO 639-3 languages")

	def __unicode__(self):
		return self.ref_name

	@property
	def name(self):
		"""Shorthand for the language's reference name."""
		return self.ref_name
