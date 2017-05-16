from setuptools import setup, find_packages
import sys, os

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
NEWS = open(os.path.join(here, 'NEWS.txt')).read()


version = '0.5.1'

install_requires = [
    'docopt',
    'pyyaml',
    'sh',
    'Sphinx>=1.6.0',
]


setup(name='tut',
      version=version,
      description="",
      long_description=README + '\n\n' + NEWS,
      classifiers=[
      ],
      keywords='',
      author='Nathan Yergler',
      author_email='nathan@yergler.net',
      url='http://github.com/nyergler/tut',
      license='BSD',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      entry_points={
          'console_scripts': [
              'tut=tut.cmd:main',
          ],
      },
      tests_require=[
          'munch',
          'sphinx-testing>=0.7.2',
      ],
      test_suite='tut.tests',
)
