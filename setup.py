from distutils.core import setup

setup(
    name='Biological Dataset Repository',
    version='1.1',
    packages=['bdr'],
    url='https://github.com/MikeWinter/bio-data-repository',
    license='GNU General Public License 2+',
    author='Michael Winter',
    author_email='Michael.Winter.2013@live.rhul.ac.uk',
    description='',
    requires=['django-bootstrap3', 'django', 'httplib2', 'locket']
)
