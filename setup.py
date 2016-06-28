# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='Beam Profiler',
    version='0.0.1',
    description='Beam profiler for summer internship at Birmingham Physics Department',
    long_description=readme,
    author='Samuel Bancroft',
    author_email='S.Bancroft@bham.ac.uk',
    url='https://github.com/spiruel/beamprofiler',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)