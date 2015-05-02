import os
from setuptools import setup

setup(
    name='django-slam',
    version='1.1',
    packages=['slam', 'slam.webinterface', 'slam.slam'],
    include_package_data=True,
    scripts=['slam/slam_cli.py'],
    install_requires=['django'],
    license='BSD License',  # example license
    description='A Django app to manage IP Address.',
    long_description='',
    url='http://www.example.com/',
    author='Y. Delalande, G. Philippon, M. Jouvin',
    author_email='',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Network Administrator',
        'License :: OSI Approved :: Apache License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        # Replace these appropriately if you are stuck on Python 2.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)