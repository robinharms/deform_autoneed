import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

requires = [
    'fanstatic',
    'deform',
    'colander',
    ]

setup(name='deform_autoneed',
      version='0.1dev',
      description='Auto include resources in deform via fanstatic.',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='Robin Harms Oredsson',
      author_email='robin@betahaus.net',
      url='https://github.com/robinharms/deform_autoneed',
      keywords='web pylons pyramid deform',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires = requires,
      tests_require = requires,
      test_suite = "deform_autoneed",
      entry_points = """\
      [fanstatic.libraries]
      deform_autoneed_lib = deform_autoneed:deform_autoneed_lib
      """,
      )
