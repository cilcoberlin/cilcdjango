
from django.template.defaultfilters import slugify
from django.utils.encoding import force_unicode
from django.utils.functional import allow_lazy
from django.utils.safestring import mark_safe
from django.utils.translation import ungettext

import re
import string

_preserve_patterns = (
	re.compile('([A-Z]{2,})'), # Acronyms
	re.compile('([a-z][A-Z])') # CamelCase
)

_quotes = (
	"\"",
	"'"
)

#-------------------------------------------------------------------------------
#  Helpers
#-------------------------------------------------------------------------------

def _preserve_text(text, matches):
	"""
	Return the portions of `text` that match the re match objects in the
	`matches` list to their original state.
	"""

	for match in matches:
		for i, group in enumerate(match.groups()):
			text = text[:match.start(i)] + group + text[match.end(i):]
	return u"".join(text)

def _process_text(value, function, first_chunk_function=None):
	"""
	Process the text contained in `value`, applying the passed function in
	`function` to each whitespace-delineated chunk within it, and applying the
	`first_chunk_function` function to the first part of the text, if one is
	specified.

	This function is used to centralize logic for custom titlecase,
	capitalization and slugifying text transformations.
	"""

	new_value = []

	#  Apply the text filter to each word in the given text, making a special
	#  check on the first word for whether or not to use a one-off function.
	for i, part in enumerate(re.split(r'\s', force_unicode(value).strip())):

		if not part:
			continue

		transform = first_chunk_function if first_chunk_function and not i else function

		#  Make sure to apply the filter to values preceded by quotes
		if part[0] in _quotes:
			append_val = "%s%s" % (part[0], transform(part[1:]))
		else:
			append_val = transform(part)

		#  If the text has sections that should be unchanged, such as acronyms,
		#  prevent these sections from being altered.
		preserve_matches = []
		for pattern in _preserve_patterns:
			match = pattern.search(part)
			if match:
				preserve_matches.append(match)
		if preserve_matches:
			append_val = _preserve_text(append_val, preserve_matches)

		new_value.append(append_val)

	return u" ".join(new_value)

#-------------------------------------------------------------------------------
#  Text Processing
#-------------------------------------------------------------------------------

def smart_capitalize(value):
	"""Capitalize each apparent sentence in the passed text of `value`."""

	return u".  ".join(
		_process_text(sentence, unicode.lower, unicode.capitalize)
		for sentence in re.split(r'\.\s', force_unicode(value))
	)
smart_capitalize = allow_lazy(smart_capitalize, unicode)

def smart_title(value):
	"""
	Return a titlecased version of the text passed as `value`, attempting to
	preserve acronyms and other formatting.

	If the passed value appears to be an excerpt, each sentence contained in the
	excerpt is capitalized.
	"""

	#  Abort if the value appears to be an excerpt, as indicated by a terminal
	#  ellipsis, and otherwise return the title-cased string
	value = force_unicode(value)
	if re.search(r'\.{3,}$', value):
		return smart_capitalize(value)
	else:
		return _process_text(value, unicode.capitalize)
smart_title = allow_lazy(smart_title, unicode)

def smart_slugify(value):
	"""
	Return a slug of the string in `value`, that will be a standard slug if the
	text is in basic ASCII characters, or a minimally processed version of the
	string, with whitespace condensed and converted to a "-" character, if it is
	in a more complex character set.
	"""

	SLUG_LENGTH_THRESHOLD_PERCENTAGE = 0.6

	#  If the length of the slugified value is less than an arbitrary percentage
	#  of the length of the full value, make no character modifications, but
	#  strip punctuation and whitespace from the value to be slugified.
	slug_value = slugify(force_unicode(value))
	if len(slug_value) < SLUG_LENGTH_THRESHOLD_PERCENTAGE * len(value):

		uni_punc   = force_unicode(string.punctuation)
		strip_punc = u''.join([' ' for punc in uni_punc])

		no_punctuation = dict(zip(map(ord, uni_punc), strip_punc))
		slug_value     = value.translate(no_punctuation).lower()

		slug_value = mark_safe(re.sub(r'\s{1,}', '-', slug_value.strip()))
	return slug_value
smart_slugify = allow_lazy(smart_slugify, unicode)

#-------------------------------------------------------------------------------
#  Text Formatting
#-------------------------------------------------------------------------------

def verbose_time_delta(delta):
	"""
	Return a verbose, human-readable representation of the datetime.timedelta
	object passed as `delta`.

	This representation of the delta is a comma-separated list of days, hour and
	minutes, or whichever of those is a non-zero value. If there is more than
	one non-zero value, the last two values are separated with an "and".
	"""

	verbose = u""
	parts   = []

	if delta:

		if delta.days:
			parts.append(ungettext("%(days)d day", "%(days)d days", delta.days) % {'days': delta.days})

		if delta.seconds:
			all_minutes = delta.seconds / 60
			hours = all_minutes / 60
			minutes = all_minutes % 60
			if hours:
				parts.append(ungettext("%(hours)d hour", "%(hours)d hours", hours) % {'hours': hours})
			if minutes:
				parts.append(ungettext("%(minutes)d minute", "%(minutes)d minutes", minutes) % {'minutes': minutes})

		#  Join the values into a comma-separated list, with the final value
		#  preceded by an "and", if there are enough parts.
		if len(parts) > 1:
			verbose = u"%(comma_parts)s and %(and_part)s" % ({
				'comma_parts': u", ".join(parts[:-1]),
				'and_part':    parts[-1]
			})
		else:
			verbose = parts[0]

	return verbose
