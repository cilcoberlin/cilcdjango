
from django.http import HttpResponse

import simplejson as json

class JsonResponse(HttpResponse):
	"""A JSON-formatted HTTP response."""

	def __init__(self, data, *args, **kwargs):
		"""
		Requires a dictionary defining the keys and values of the JSON object to
		be returned as the first argument.

		This can accept an optional `i_frame` keyword argument, indicating that
		the JSON response is going to be first received by an iframe element.
		"""

		for_iframe = kwargs.pop('i_frame', False)
		if not for_iframe:
			kwargs['mimetype'] = "application/json"
		super(JsonResponse, self).__init__(*args, **kwargs)

		#  Format the response as JSON, and, if the response is being embedded
		#  in an i_frame, which can happen when uploading files via ajax, wrap
		#  the content in a textarea
		if 'success' not in data:
			data['success'] = True
		json.dump(data, fp=self)
