#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.md') as readme_file:
    readme = readme_file.read()

with open('HISTORY.md') as history_file:
    history = history_file.read()

requirements = [
    'jinja2==2.8',
    'paramiko==1.16.0',
    'path.py==8.1.2',
    'plumbum==1.6.6'

]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='cubric',
    version='0.1.0',
    description="A higher level deployment/orchestration toolkit",
    long_description=readme + '\n\n' + history,
    author="Ivo van der Wijk",
    author_email='cubric@in.m3r.nl',
    url='https://github.com/iivvoo/cubric',
    packages=[
        'cubric',
    ],
    package_dir={'cubric':
                 'cubric'},
    include_package_data=True,
    install_requires=requirements,
    license="ISCL",
    zip_safe=False,
    keywords='cubric',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
