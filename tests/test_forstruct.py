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

"""Tests for the main module when used with structlog."""

import logging

import pytest
import structlog

from logassert import Exact, Multiple, Sequence, NOTHING

logger = structlog.get_logger()

# -- Basic usage

def test_basic_simple_assert_ok_simple(logs):
    logger.debug("test")
    assert "test" in logs.any_level


def test_basic_simple_assert_ok_with_kwargs(logs):
    logger.debug("test", foo=65, extra="bar")
    assert {"event": "test", "foo": 65, "extra": "bar"} in logs.any_level


def test_basic_simple_negated_assert_(logs):
    logger.debug("aaa")
    assert "aaa" not in logs.warning  # different than logged
    assert "bbb" not in logs.any_level  # checking other text in any level
    assert "bbb" not in logs.debug  # checking other text in same level


def test_reset(logs):
    logger.debug("foobar")
    assert "foobar" in logs.debug
    logs.reset()
    assert "foobar" not in logs.debug

