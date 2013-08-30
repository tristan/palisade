
from setuptools import setup

setup(
    name='Palisade',
    version='0.1.0',
    author='Tristan King',
    author_email='tristan.king@gmail.com',
    packages=['palisade'],
    url='http://github.com/tristan/palisade',
    description='Flask bluprints providing OAuth login capabilities for various OAuth providers.',
    long_description=open('README.md').read(),
    install_requires = [ 'flask', 'rauth', 'simplejson' ]
)
