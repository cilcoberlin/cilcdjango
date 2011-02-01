
from django.forms.widgets import flatatt
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

import re
import simplejson as json
import urllib

def embed_flash(url, id, width, height, flashvars={}, attributes={}, version="10"):
	"""Return markup for directly embedding flash into an HTML document."""

	#  Make the SWF play well with scripts and other page graphics
	params = {
		'allowscriptaccess': "always",
		'wmode': "transparent",
		'allowfullscreen': "true"
	}

	#  Build the markup for optional parameters
	object_params = "\n".join([
		u'<param name="%(name)s" value="%(value)s" />' % {
			'name': key,
			'value': value
		} for key, value in params.iteritems()
	])

	markup = """
		<object classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000"
				id="%(id)s" width="%(width)d" height="%(height)d" %(attributes)s
				codebase="http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab">
			<param name="movie" value="%(url)s" />
			<param name="flashvars" value="%(flashvars)s" />
			%(object_params)s
			<embed src="%(url)s" width="%(width)d" height="%(height)d" name="%(id)s"
				%(embed_params)s %(attributes)s
				flashvars="%(flashvars)s"
				type="application/x-shockwave-flash" pluginspage="http://www.macromedia.com/go/getflashplayer">
			</embed>
		</object>
	""" % {
		'url': url,
		'id': id,
		'height': height,
		'width': width,
		'flashvars': re.sub(r'&', '&amp;', urllib.urlencode(flashvars)),
		'object_params': object_params,
		'embed_params': flatatt(params),
		'attributes': flatatt(attributes),
	}

	return mark_safe(markup)
