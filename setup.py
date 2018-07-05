from setuptools import setup
from sys import version_info

setup(name='brstores',
      version='0.8.3',
      description='Directory synchronizer Python Application',
      url='https://github.com/kenlowrie/brstores',
      author='Ken Lowrie',
      author_email='ken@kenlowrie.com',
      license='Apache',
      packages=['brstores'],
      install_requires=['pylib_kenl380'],
      entry_points = {
        'console_scripts': ['br=brstores.br:brsync_entry',
                            'br{}=brstores.br:brsync_entry'.format(version_info.major)
                           ],
      },
      zip_safe=False)
