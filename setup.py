# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup_requires = (
    'pytest-runner',
    )
install_requires = (
    )
tests_require = [
    'pytest',
    'WebTest >= 1.3.1',
    ]
extras_require = {
    'test': tests_require,
    }
description = "Connexions Content Manager Press"
with open('README.rst', 'r') as readme:
    long_description = readme.read()

setup(
    name='cnx-press',
    version='0.0.0',
    author='Connexions team',
    author_email='info@cnx.org',
    url="https://github.com/connexions/cnx-press",
    license='AGPL, See also LICENSE.txt',
    description=description,
    long_description=long_description,
    setup_requires=setup_requires,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require=extras_require,
    test_suite='press.tests',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'press.tests': ['data/**/*.*'],
        },
    entry_points="""\
    [paste.app_factory]
    main = press.main:paste_app_factory
    [console_scripts]
    """,
    )
