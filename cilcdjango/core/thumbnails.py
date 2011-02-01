
def alphacolorspace(im, requested_size, opts):
	"""Add support for the alpha channel to the sorl thumbnail module."""
	if im.mode != "RGBA":
		im = im.convert("RGBA")
	return im
alphacolorspace.valid_options = ()
