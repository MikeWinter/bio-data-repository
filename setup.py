from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup

setup(
    name='Biological Dataset Repository',
    version='2.0a0',
    packages=['bdr'],
    url='https://github.com/MikeWinter/bio-data-repository',
    license='GNU General Public License 2+',
    author='Michael Winter',
    author_email='Michael.Winter.2013@live.rhul.ac.uk',
    description='',
    requires=['django_bootstrap3', 'django', 'httplib2', 'locket'],
    entry_points={'bdr.formats': ['raw = bdr.formats.raw',
                                  'simple = bdr.formats.simple']},
)
