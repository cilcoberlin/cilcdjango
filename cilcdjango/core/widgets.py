
from cilcdjango.core.media import SharedMediaMixin, make_shared_media_url
from cilcdjango.core.util import get_app_setting

from django import forms
from django.conf import settings
from django.core.urlresolvers import reverse
from django.forms.widgets import flatatt
from django.utils.encoding import force_unicode, smart_unicode
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

import datetime
import re

#-------------------------------------------------------------------------------
#  Helpers
#-------------------------------------------------------------------------------

def _update_attr_classes(attrs, classes):
	"""
	Add the classes contained in the `classes` iterable to the "class" key of
	the attributes passed to the widget's constructor in the `attrs` dict.
	"""
	if not attrs:
		attrs = {}
	attrs['class'] = u" ".join(set(re.split(r'\s+', attrs.get('class', '')) + classes)).strip()
	return attrs

#-------------------------------------------------------------------------------
#  Date / Time Widgets
#-------------------------------------------------------------------------------

class DatePickerWidget(forms.DateTimeInput, SharedMediaMixin):
	"""A widget that lets a user use a JavaScript date picker to select a date."""

	def render(self, name, value, attrs=None):

		#  Attempt to turn a previous date value into one capable of being set
		#  as the input field's value attribute.
		try:
			previous_date = value.strftime(self.format)
		except AttributeError:
			if value is None or value == "None":
				previous_date = ""
			else:
				previous_date = value
		current_value = "value='%s'" % escape(previous_date)

		#  Render the widget as a simple text field, which is transformed into a
		#  datepicker widget through JavaScript
		form_html = [u"<input type='text' name='%s' id='id_%s' size='12' class='uses-date-picker' %s />" % (name, name, current_value) ]
		return mark_safe(u'\n'.join(form_html))

	class SharedMedia:

		css = {
			'screen': ('core/css/libs/jquery_ui/jquery.ui.css',)
		}

		js = (
			'core/js/libs/jquery/jquery.ui.js',
			'core/js/widgets/date_picker.js'
		)

class SimpleTimeWidget(forms.TextInput):
	"""A simple time widget that ignores seconds."""

	_CLOCK_ICON = "core/images/clock_icon_tiny.png"
	_ICON_CLASSES = ["clock-icon"]

	def __init__(self, *args, **kwargs):

		default_args = {'size': 4, 'class': 'dt-time-input'}
		try:
			kwargs['attrs'].update(default_args)
		except KeyError:
			kwargs['attrs'] = default_args
		super(SimpleTimeWidget, self).__init__(*args, **kwargs)

		self.time_format = "%H:%M"

	def render(self, name, value, attrs=None):
		"""Show the field's time value in HH:MM format."""

		final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)

		#  Attempt to transform an existing time value into a value capable of
		#  being an attribute of the input tag that this widget is rendered as.
		try:
			value = value.strftime(self.time_format)
		except AttributeError:
			try:
				value = datetime.datetime.strptime(value, "%H:%M").time().strftime(self.time_format)
			except (ValueError, AttributeError, TypeError):
				value = ''
		final_attrs['value'] = force_unicode(value)
		return mark_safe(
			u'<input%(input)s /> <img src="%(icon_src)s" class="%(icon_class)s" alt="%(icon_alt)s" />' % {
				'input': flatatt(final_attrs),
				'icon_src': make_shared_media_url(self._CLOCK_ICON),
				'icon_class': u" ".join(self._ICON_CLASSES),
				'icon_alt': _("clock icon")
			})


class DateTimeWidget(forms.MultiWidget):
	"""A widget that encapsulates a date picker and a time input."""

	def __init__(self, *args, **kwargs):

		kwargs['widgets'] = [ DatePickerWidget(format='%m/%d/%Y'), SimpleTimeWidget() ]
		super(DateTimeWidget, self).__init__(*args, **kwargs)

	def decompress(self, value):
		"""
		Break the datetime.datetime instance in `value` into its date and time
		components.
		"""
		try:
			return [value.date(), value.time()]
		except AttributeError:
			return [None, None]

#-------------------------------------------------------------------------------
#  Text Widgets
#-------------------------------------------------------------------------------

class RichTextEditorWidget(forms.Textarea, SharedMediaMixin):
	"""A textarea that uses CKEditor to allow the user to input rich text."""

	def __init__(self, editor_type="default", auto_focus=False, attrs=None):

		super(RichTextEditorWidget, self).__init__(attrs)
		self.auto_focus  = auto_focus
		self.editor_type = editor_type

	def render(self, name, value, attrs=None):

		final_attrs = self.build_attrs(attrs)
		final_attrs['name'] = name

		#  Set custom classes for the textarea for use by the JavaScript code
		classes = getattr(final_attrs, 'class', [])
		classes.append("uses-rte")
		classes.append("editor-%s" % self.editor_type)
		if self.auto_focus:
			classes.append('auto-focus')
		final_attrs['class'] = " ".join(classes)

		html = [u'<textarea%s>%s</textarea>' % (flatatt(final_attrs), escape(smart_unicode(value or '')))]
		return mark_safe(u'\n'.join(html))

	class SharedMedia:

		js = (
			'core/js/libs/ckeditor/ckeditor.js',
			get_app_setting('RTE_CONFIG_FILE'),
			'core/js/widgets/rich_text.js'
		)

class WordCounterWidget(forms.Textarea, SharedMediaMixin):
	"""
	A textarea that counts the number of words entered and updates this count as
	the user types.
	"""

	_CSS_CLASSES = {
		'widget':    "uses-word-counter",
		'max_words': "max-words_",
		'min_words': "min-words_"
	}

	def __init__(self, min_words=None, max_words=None, attrs=None):
		"""
		Add special classes to the textarea that are used by JavaScript to
		generate the markup for the word counter.
		"""

		#  Add classes for the max and min words, if they are specified
		classes = []
		if min_words or max_words:
			classes.append(self._CSS_CLASSES['widget'])
		if min_words:
			classes.append("%s%s" % (self._CSS_CLASSES['min_words'], min_words))
		if max_words:
			classes.append("%s%s" % (self._CSS_CLASSES['max_words'], max_words))

		super(WordCounterWidget, self).__init__(
			attrs=_update_attr_classes(attrs, classes)
		)

	class SharedMedia:

		js = (
			'core/js/widgets/word_counter.js',
		)
