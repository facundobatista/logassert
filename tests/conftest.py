# Copyright 2024 Facundo Batista
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

"""Tests helpers."""

import pytest

# to be able to use `logs` in our unit tests
pytest_plugins = [
    "logassert.pytest_plugin",
]


@pytest.fixture
def integtest_runner(testdir, pytestconfig):
    """Provide an easy way of running an integration test."""

    def run(real_test_code):
        # create a temporary conftest.py file
        plugin_fpath = pytestconfig.rootdir / 'logassert' / 'pytest_plugin.py'
        with plugin_fpath.open('rt', encoding='utf8') as fh:
            testdir.makeconftest(fh.read())

        # create a temporary pytest test file
        testdir.makepyfile(real_test_code)

        # run the test with pytest
        result = testdir.runpytest()

        return result

    return run
