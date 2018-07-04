from setuptools import setup

setup(name='brstores',
      version='0.8.3',
      description='Directory synchronizer Python Application',
      url='https://github.com/kenlowrie/brstores',
      author='Ken Lowrie',
      author_email='ken@kenlowrie.com',
      license='Apache',
      packages=['brstores'],
      entry_points = {
        'console_scripts': ['br=brstores.br:brsync_entry'],
      },
      zip_safe=False)
