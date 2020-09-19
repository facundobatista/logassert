#!/usr/bin/env python3

# Copyright 2015-2020 Facundo Batista
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser  General Public License version 3, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# For further info, check  https://github.com/facundobatista/logassert

"""Build tar.gz for logassert."""

from setuptools import setup

setup(
    name='logassert',
    version='5',
    license='LGPL-3',
    author='Facundo Batista',
    author_email='facundo@taniquetil.com.ar',
    description='Simple but powerful assertion and verification of logged lines.',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url='https://github.com/facundobatista/logassert',

    # the following makes a plugin available to pytest
    entry_points={"pytest11": ["logassert = logassert.pytest_plugin"]},

    packages=["logassert"],
    install_requires=['setuptools'],
    python_requires='>=3.5',

    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 5 - Production/Stable',

        'Framework :: Pytest',

        'Environment :: Console',

        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',

        'License :: OSI Approved :: GNU General Public License (GPL)',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',

        'Natural Language :: English',
        'Natural Language :: Spanish',

        'Operating System :: MacOS',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',

        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',

        'Topic :: Software Development',
        'Topic :: Utilities',
    ],
)
