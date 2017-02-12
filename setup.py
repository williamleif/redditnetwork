from setuptools import setup
from setuptools import find_packages

setup(name='redditnetwork',
      version='1.0',
      description='Code for accessing processing Reddit data',
      author='William L. Hamilton',
      author_email='will.leif.hamiltion@gmail.com',
      license='MIT',
      install_requires=['spacy==1.2.0',
                        'networkx',
                        'numpy',
                        'isoweek',
                        'pandas',
                        'nltk'
                        ],
      package_data={'redditnetwork': ['README.md']},
      packages=find_packages())
