
from setuptools import setup, find_packages

setup(
	name='cilcdjango',
	version=__import__('cilcdjango').__version__,
	description='Python helper modules for Django applications made by the Oberlin CILC.',
	author='Justin Locsei',
	author_email='justin.locsei@oberlin.edu',
	url='https://github.com/cilcoberlin/cilcdjango',
	download_url='https://github.com/cilcoberlin/cilcdjango/zipball/master',
	packages=find_packages(),
	package_data={'': ["*.*"]},
	include_package_data=True,
	zip_safe=False,
	classifiers=[
		'Development Status :: 3 - Alpha',
		'Environment :: Web Environment',
		'Intended Audience :: Developers',
		'Operating System :: OS Independent',
		'Programming Language :: Python',
		'Framework :: Django'
	]
)
