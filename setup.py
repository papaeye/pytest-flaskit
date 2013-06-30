import os.path

from setuptools import setup


here = os.path.dirname(os.path.abspath(__file__))
version = next((line.split('=')[1].strip().replace("'", '')
                for line in open(os.path.join(here, 'pytest_flaskit.py'))
                if line.startswith('__version__ = ')),
               '0.0.dev0')


setup(name='pytest-flaskit',
      version=version,
      description='A collection of pytest fixtures for Flask apps',
      author='papaeye',
      author_email='papaeye@gmail.com',
      url='http://github.com/papaeye/pytest-flaskit',
      py_modules=['pytest_flaskit'],
      include_package_data=True,
      install_requires=[
          'Flask>=0.10',
          'blinker',
          'pytest',
      ],
      tests_require=[
      ],
      zip_safe=False,
      keywords='pytest flask',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: BSD License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
      ],
      platforms='any',
      license='BSD License',
      entry_points={
          'pytest11': ['flaskit = pytest_flaskit']
      })
