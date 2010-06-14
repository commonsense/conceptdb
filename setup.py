#!/usr/bin/env python
from setuptools import setup, find_packages

packages = find_packages(exclude=['maint'])
version_str = '0.1'

setup(  name='ConceptDB',
        version=version_str,
        description='An extensible database for common sense semantics',
        author='Robert Speer, Catherine Havasi, Jason Alonso, and Kenneth Arnold',
        author_email='conceptnet@media.mit.edu',
        url='http://conceptnet.media.mit.edu/',
        packages=packages,
        include_package_data=False,
        namespace_packages = ['csc'],
        install_requires=['mongoengine'],

        # Metadata
        license = "GPL v3",
        )
