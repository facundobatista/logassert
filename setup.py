#!/usr/bin/env python3.4

# Copyright 2015 Facundo Batista
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

from distutils.core import setup

setup(
    name='logassert',
    version='1',
    license='LGPL-3',
    author='Facundo Batista',
    author_email='facundo@taniquetil.com.ar',
    description='Log Assertion.',
    long_description=open('README.rst').read(),
    url='https://github.com/facundobatista/logassert',

    packages=["logassert"],
    install_requires=['setuptools'],
)
