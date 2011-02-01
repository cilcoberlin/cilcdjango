
class RendererType(type):
	"""Metaclass for a file or URL renderer."""

	def __init__(cls, name, base, attrs):
		"""Assemble a list of the available renderers."""

		super(RendererType, cls).__init__(cls, name, base, attrs)

		#  Build a list of all renderers that use this as a base type
		if not hasattr(cls, 'renderers'):
			cls.renderers = []
		else:
			cls.renderers.append(cls)
