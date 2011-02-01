
from cilcdjango.core.users import LDAPConnection
from cilcdjango.core.widgets import *

from django import forms
from django.utils.translation import ugettext as _

import datetime
from lxml import etree
from lxml.etree import XMLSyntaxError
import lxml.html
from lxml.html.clean import Cleaner
import re

#-------------------------------------------------------------------------------
#  User Fields
#-------------------------------------------------------------------------------

class UserMultipleChoiceField(forms.ModelMultipleChoiceField):
	"""A multiple choice field for Users that shows a user's full name."""

	def label_from_instance(self, user):
		return user.get_full_name()

class UserMultipleChoiceField(forms.ModelMultipleChoiceField):
	"""A choice field for Users that shows a user's full name."""

	def label_from_instance(self, user):
		return user.get_full_name()

class TNumbersField(forms.CharField):
	"""
	A field that accepts a list of student T numbers and returns a dictionary of
	the user information returned for each T number.
	"""

	widget = forms.Textarea()

	def __init__(self, *args, **kwargs):

		if 'label' not in kwargs:
			kwargs['label'] = _('student T numbers')
		if 'help_text' not in kwargs:
			kwargs['help_text'] = _("separate the T numbers using commas, spaces or line breaks")

		super(TNumbersField, self).__init__(*args, **kwargs)

	def clean(self, value):
		"""
		Verify that every T number is valid and return a list of the T numbers.

		A valid T number is in the form: T12345678.
		"""

		t_list  = super(TNumbersField, self).clean(value)
		t_list  = re.sub(r'\n', '', t_list.strip())
		valid_t = re.compile(r'^T\d{8}$')

		#  Normalize the input into a list, and make sure that each number
		#  provided is a T number, which is a "T" followed by 8 digits.
		t_numbers = []
		for t_number in re.split(r'[\,\s]', t_list):
			if t_number:
				clean_t = t_number.strip().upper()
				if valid_t.search(clean_t):
					t_numbers.append(clean_t)
				else:
					raise forms.ValidationError(_("the T number %(tnumber)s is not valid") % {
						'tnumber': clean_t
					})
		self._t_numbers = t_numbers
		return t_numbers

	def verify_users(self):
		"""
		Return a dict whose keys will be a user's T number and whose values will
		be the dictionary of LDAP values returned from an LDAP lookup of the
		user.

		This is called after the field has been cleaned and a list of
		valid-format T numbers has been generated, and will raise a validation
		error if any T number does not map to a valid user.
		"""

		#  Get information on each user, and raise an error if a T number
		#  returns no information on a user
		users = {}
		if self._t_numbers:
			ldap_conn = LDAPConnection()
			for t_number in self._t_numbers:
				info = ldap_conn.get_info_from_tnumber(t_number)
				if info:
					users[t_number] = info
				else:
					raise forms.ValidationError(_("no user could be found with the T number %(tnumber)s") % {
						'tnumber': t_number
					})
		return users

#-------------------------------------------------------------------------------
#  Yes / No Boolean Field
#-------------------------------------------------------------------------------

class YesNoField(forms.ChoiceField):
	"""
	A field that transforms Django's default checkbox for a boolean type into a
	radio button with user-defined text for the labels.
	"""

	field_classes = ['yes-no']

	def __init__(self, *args, **kwargs):
		"""Create a ChoiceField as a container for boolean values."""
		choices = [(True, kwargs.pop('yes', _('yes')).title()), (False, kwargs.pop('no', _('no')).title())]
		if 'required' not in kwargs:
			kwargs['required'] = False
		super(YesNoField, self).__init__(choices, *args, **kwargs)
		self.widget = forms.RadioSelect(choices=choices, attrs={'class': "boolean-radio"})

	def clean(self, value):
		"""Return the user's choice as a boolean value or as None, if left blank."""
		if value:
			if value == 'False':
				return False
			else:
				return True
		if self.required:
			raise forms.ValidationError('You must choose yes or no')
		else:
			return None

#-------------------------------------------------------------------------------
#  Date and Date / Time Fields
#-------------------------------------------------------------------------------

class PickedDateField(forms.DateField):
	"""A date field that uses a JavaScript date picker widget."""

	def __init__(self, *args, **kwargs):
		super(PickedDateField, self).__init__(*args, **kwargs)
		self.widget = DatePickerWidget(format='%m/%d/%Y')

class PickedDateTimeField(forms.MultiValueField):
	"""A field that combines a date picker and a field for a time."""

	def __init__(self, *args, **kwargs):
		"""Initialize the two separate date and time fields."""

		#  Build our hour and minute fields
		date_field = PickedDateField()
		time_field = forms.TimeField(input_formats=['%H:%M'])
		kwargs['fields'] = (date_field, time_field)
		super(PickedDateTimeField, self).__init__(*args, **kwargs)

		#  Configure the widgets for display
		self.widget = DateTimeWidget()

	def compress(self, data_list):
		"""Combine the hours and minutes into minutes."""
		try:
			date_time = datetime.datetime.combine(data_list[0], data_list[1])
		except IndexError:
			date_time = None
		return date_time

#-------------------------------------------------------------------------------
#  Rich Text Editor Field
#-------------------------------------------------------------------------------

class RichTextCleaner(Cleaner):
	"""Custom cleaner for the rich text editor markup."""

	embedded = False

class RichTextEditorField(forms.CharField):
	"""
	A field that shows a textarea that is transformed into a rich text editor
	using CKEditor once the page has been loaded.

	The tags defined in `_STRIP_EMPTY_ELEMENTS` will be removed from the
	document tree if they contain neither child tags nor text. The
	`_REPLACE_ELEMENTS` dict is keyed by tags to replace, and has a value in the
	form of ('replace_with_tag', {'attr1': 'val1'}).
	"""

	_HAS_TEXT_SEARCH = re.compile(r'[^\s]')
	_STRIP_EMPTY_ELEMENTS = (
		'div', 'p',
		'b', 'em', 'i', 'span', 'strong'
	)
	_REPLACE_ELEMENTS = {
		'u': ('span', {'class': "underline"})
	}

	def __init__(self, *args, **kwargs):

		#  Pass through RTE widget arguments to the RTE widget
		self.must_break = True
		editor_type = kwargs.pop('editor_type', None)
		auto_focus  = kwargs.pop('auto_focus', None)
		widget_args = {}
		if editor_type:
			widget_args['editor_type'] = editor_type
		if auto_focus:
			widget_args['auto_focus'] = auto_focus

		#  Create the field and make it use the RTE widget
		super(RichTextEditorField, self).__init__(*args, **kwargs)
		self.widget = RichTextEditorWidget(**widget_args)

	def clean(self, value):
		"""Strip out needless markup and whitespace from the editor's HTML."""

		#  Strip excess markup
		value = value or u""
		value = re.sub(r'\n|\r\n|\r', '', value)  # Line breaks
		value = re.sub(r'\&nbsp;', ' ', value)    # Non-breaking spaces
		value = re.sub(r'\s+', ' ', value)        # Excess whitespace
		value = re.sub(r'\&\#\d+;', '', value)    # Numbered entities

		#  Convert the value to an element tree and remove elements on our
		#  blacklist that have no children and no text, wrapping the value in a
		#  dummy html fragment if we were unable to parse it the first time,
		#  which can happen with tagless or blank values
		try:
			tree = lxml.html.fromstring(value)
		except XMLSyntaxError:
			tree = lxml.html.fromstring("<div>%s</div>" % value)
		for tag in tree.xpath(".//*"):
			if tag.tag in self._STRIP_EMPTY_ELEMENTS and not len(tag) and not self._HAS_TEXT_SEARCH.search(tag.text_content()):
				tag.drop_tree()

		#  Replace any replaceable elements specified in our list
		for replace_tag, replace_with in self._REPLACE_ELEMENTS.iteritems():
			for tag in tree.xpath(".//%s" % replace_tag):
				tag.tag = replace_with[0]
				for attr, val in replace_with[1].iteritems():
					tag.attrib[attr] = val

		#  Run the processed tree through lxml.html's native cleaner
		cleaner = RichTextCleaner()
		cleaner.clean_html(tree)

		#  If the tree is not empty, or if the field is not required, return
		#  the user input as properly formatted XHTML, erroring out otherwise
		if not self.required or self._HAS_TEXT_SEARCH.search(tree.text_content()):
			return lxml.html.tostring(tree, pretty_print=True, method="xml").strip()
		else:
			raise forms.ValidationError(_("you must enter text in this field"))

#-------------------------------------------------------------------------------
#  Word Counter Field
#-------------------------------------------------------------------------------

class WordCounterField(forms.CharField):
	"""A field that updates the user's current word count through JavaScript."""

	def __init__(self, min_words=None, max_words=None, hard_limit=False, *args, **kwargs):
		super(WordCounterField, self).__init__(*args, **kwargs)
		self.widget = WordCounterWidget(min_words=min_words, max_words=max_words)
		self._min_words = min_words or 0
		self._max_words = max_words or 0
		self._hard_limit = hard_limit

	def clean(self, value):
		"""
		Make sure that, if a hard limit has been set on the word count, the
		user cannot submit if the word count is outside of the given bounds.
		"""

		#  Check the current word count against the bounds and raise needed errors
		if self._hard_limit:
			word_count = len(re.split(r'[^\s]\s+?[^\s]', value)) if value else 0
			if word_count < self._min_words:
				raise forms.ValidationError(_("You must write at least %(minimum)d words.  You have currently written %(current)d." % {'minimum': self._min_words, 'current': word_count}))
			if self._max_words and word_count > self._max_words:
				raise forms.ValidationError(_("You cannot write more than %(maximum)d words.  You have currently written %(current)d." % {'maximum': self._max_words, 'current': word_count}))

		return value
