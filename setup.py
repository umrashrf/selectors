import re

from setuptools import setup, find_packages


(version, ) = re.findall(r"__version__[^=]*=[^']*[']([^']+)[']",
                        open('selectors/__init__.py').read())


setup(
    name='Selectors',
    version=version,
    url='http://github.com/scrapy/selectors',
    description='Selectors used by Scrapy framework',
    long_description=open('README.md').read(),
    author='Selectors developers',
    maintainer='Scrapy developers',
    maintainer_email='info@scrapy.org',
    license='BSD',
    packages=find_packages(exclude=('tests', 'tests.*')),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'lxml',
        'w3lib>=1.8.0',
        'cssselect>=0.9',
    ],
)
