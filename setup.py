from distutils.core import setup


version = __import__('fabdeploy').get_version()
readme = open('README').read()


setup(
    name='django-fabdeploy-plus',
    version=version.replace(' ', '-'),
    description='Fabric deployment for Django',
    long_description=readme,
    author='Vladimir Mihailenco',
    author_email='vladimir.webdev@gmail.com',
    url='https://bitbucket.org/vladimir_webdev/fabdeploy',
    packages=['fabdeploy'],
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
