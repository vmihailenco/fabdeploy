#!/usr/bin/env python

from distutils.core import setup


version = __import__('fabdeploy').get_version()
readme = open('README.rst').read()


setup(
    name='django-fabdeploy-plus',
    version=version.replace(' ', '-'),
    description='Fabric deployment for Django',
    long_description=readme,
    author='Vladimir Mihailenco',
    author_email='vladimir.webdev@gmail.com',
    url='https://github.com/vmihailenco/fabdeploy/',
    packages=['fabdeploy'],
    package_data={'fabdeploy': [
        'config_templates/supervisor/*.*',
        'config_templates/init/*.*',
        'config_templates/*.*',
    ]},
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
