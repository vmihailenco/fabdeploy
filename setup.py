from distutils.core import setup


setup(
    name='django-fabdeploy-plus',
    version='0.1.0',
    description='Django fabdeploy plus',
    author='Vladimir Mihailenco',
    author_email='vladimir.webdev@gmail.com',
    url='',
    install_requires=['fabric', 'jinja2'],
    packages=['fab_deploy'],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
