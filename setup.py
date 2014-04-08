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
      version='0.2.1b',
      description='Auto include resources in deform via Fanstatic.',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        ],
      author='Robin Harms Oredsson',
      author_email='robin@betahaus.net',
      url='https://github.com/robinharms/deform_autoneed',
      keywords='web colander deform fanstatic',
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
