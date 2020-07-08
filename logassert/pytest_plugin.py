# Copyright 2020 Facundo Batista
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

"""Integration to be a fixture of pytest."""

from logassert import logassert

import pytest

print("=========== wtf 0")

@pytest.fixture()
def logged(request):
    """Provide the logassert functionality through a fixture."""
    print("=========== wtf 1")
    return logassert.FixtureLogChecker()
