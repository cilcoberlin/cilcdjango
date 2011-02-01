
class AjaxError(Exception):
	"""
	An error that can be raised and properly handled by any view decorated with
	the @ajax_view decorator.

	An Ajax view that raises this error will return a JSON response containing
	the value of the raised error.
	"""

	def __init__(self, *args, **kwargs):
		"""
		Can accept a `for_iframe` kwarg to specify if the error is being raised
		by a view that returns its data in an IFrame, such as a view that deals
		with Ajax file uploads.
		"""
		self.i_frame = kwargs.pop('i_frame', False)
		super(AjaxError, self).__init__(*args, **kwargs)
