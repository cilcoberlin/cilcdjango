
from django.utils.translation import ugettext_lazy as _

from cilcdjango.core.exceptions import AjaxError

def get_object_or_none(Model, **kwargs):
	"""Return the object matching the kwargs or return None."""
	try:
		return Model.objects.get(**kwargs)
	except Model.DoesNotExist:
		return None

def get_object_or_ajax_error(Model, **kwargs):
	"""Return the object matching the kwargs or raise an Ajax error."""
	try:
		return Model.objects.get(**kwargs)
	except Model.DoesNotExist:
		raise AjaxError(_("unable to find a suitable %(model)s model") % {
			'model': Model.__name__})
