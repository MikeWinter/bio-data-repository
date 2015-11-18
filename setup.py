# Bootstrap the setuptools package.
from ez_setup import use_setuptools
use_setuptools()

# noinspection PyPep8
from setuptools import find_packages, setup

setup(
    name='bio-data-repository',
    description='Biological Dataset Repository: a simple archival and retrieval system for biological data.',
    version='2.0a4',
    author='Michael Winter',
    author_email='Michael.Winter.2013@live.rhul.ac.uk',
    url='https://github.com/MikeWinter/bio-data-repository',
    py_modules=['ez_setup'],
    packages=find_packages(exclude=['repository']),
    include_package_data=True,
    install_requires=['django_bootstrap3', 'django', 'httplib2', 'locket'],
    entry_points={'bdr.formats': ['raw    = bdr.formats.raw',
                                  'simple = bdr.formats.simple'],
                  'bdr.views.formats': ['raw    = bdr.formats.raw:views',
                                        'simple = bdr.formats.simple:views']},
    classifiers=['Development Status :: 3 - Alpha',
                 'Environment :: Web Environment',
                 'Framework :: Django :: 1.6',
                 'Intended Audience :: Science/Research',
                 'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
                 'Natural Language :: English',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python :: 2.7',
                 'Topic :: Scientific/Engineering :: Bio-Informatics']
)
