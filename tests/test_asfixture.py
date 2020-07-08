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

"""Tests for the main module when used as a pytest fixture."""

import logging
import os

import pytest

from logassert.logassert import FixtureLogChecker


@pytest.fixture
def logger():
    lgr = logging.getLogger()
    lgr.handlers = []
    return lgr


# -- Basic usage

def test_basic_simple_assert_ok(logger):
    flc = FixtureLogChecker()
    logger.debug("test")
    flc.assert_logged("test")


def test_basic_simple_assert_ok_extras(logger):
    flc = FixtureLogChecker()
    formatter = logging.Formatter("%(message)s %(foo)s")
    for h in logger.handlers:
        h.setFormatter(formatter)
    logger.debug("test", extra={'foo': 'bar'})
    flc.assert_logged("test bar")


def test_basic_simple_assert_ok_with_replaces(logger):
    flc = FixtureLogChecker()
    logger.debug("test %d %r", 65, 'foobar')
    flc.assert_logged("test", "65", "foobar")


def test_basic_simple_assert_fail(logger):
    flc = FixtureLogChecker()
    logger.debug("test")
    with pytest.raises(AssertionError) as cm:
        flc.assert_logged("test2")
    assert str(cm.value) == (
        "Tokens ('test2',) not found, all was logged is...\n"
        "    DEBUG     'test'")


def test_basic_simple_assert_fail_with_replaces():
    flc = FixtureLogChecker()
    logger = logging.getLogger()
    logger.debug("test %d %r", 65, 'foobar')
    with pytest.raises(AssertionError) as cm:
        flc.assert_logged("test", "pumba")
    assert str(cm.value) == (
        "Tokens ('test', 'pumba') not found, all was logged is...\n"
        "    DEBUG     \"test 65 'foobar'\"")


def test_basic_avoid_delayed_messaging():
    flc = FixtureLogChecker()

    class Exploding:
        """Explode on delayed str."""
        should_explode = False

        def __str__(self):
            if self.should_explode:
                raise ValueError("str exploded")
            return "didn't explode"

    # log something using the Exploding class
    exploding = Exploding()
    logger = logging.getLogger()
    logger.debug("feeling lucky? %s", exploding)

    # now flag the class to explode and check
    exploding.should_explode = True
    flc.assert_logged("feeling lucky", "didn't explode")


# -- Levels

def test_levels_assert_different_level_ok_debug(logger):
    flc = FixtureLogChecker()
    logger.debug("test")
    flc.assert_debug("test")


def test_levels_assert_different_level_ok_info(logger):
    flc = FixtureLogChecker()
    logger.info("test")
    flc.assert_info("test")


def test_levels_assert_different_level_ok_error(logger):
    flc = FixtureLogChecker()
    logger.error("test")
    flc.assert_error("test")


def test_levels_assert_different_level_ok_exception(logger):
    flc = FixtureLogChecker()
    try:
        raise ValueError("test error")
    except ValueError:
        logger.exception("test message")
    flc.assert_error("test error")
    flc.assert_error("test message")
    flc.assert_error("ValueError")


def test_levels_assert_different_level_ok_warning(logger):
    flc = FixtureLogChecker()
    logger.warning("test")
    flc.assert_warning("test")


def test_levels_assert_different_level_fail_oneway(logger):
    flc = FixtureLogChecker()
    logger.warning("test")
    with pytest.raises(AssertionError) as cm:
        flc.assert_debug("test")
    assert str(cm.value) == (
        "Tokens ('test',) not found in DEBUG, all was logged is...\n"
        "    WARNING   'test'")


def test_levels_assert_different_level_fail_inverse(logger):
    flc = FixtureLogChecker()
    logger.debug("test")
    with pytest.raises(AssertionError) as cm:
        flc.assert_warning("test")
    assert str(cm.value) == (
        "Tokens ('test',) not found in WARNING, all was logged is...\n"
        "    DEBUG     'test'")


# -- Negative assertions

def test_negative_simple_ok(logger):
    flc = FixtureLogChecker()
    logger.debug("test")
    flc.assert_not_logged("other")


def test_negative_simple_fail(logger):
    flc = FixtureLogChecker()
    logger.info("test")
    with pytest.raises(AssertionError) as cm:
        flc.assert_not_logged("test")
    assert str(cm.value) == "Tokens ('test',) found in the following record:  INFO  'test'"


def test_negative_level_debug_ok(logger):
    flc = FixtureLogChecker()
    logger.info("test")
    flc.assert_not_debug("test")


def test_negative_level_debug_fail(logger):
    flc = FixtureLogChecker()
    logger.debug("test")
    with pytest.raises(AssertionError) as cm:
        flc.assert_not_debug("test")
    assert str(cm.value) == "Tokens ('test',) found in the following record:  DEBUG  'test'"


def test_negative_level_info(logger):
    flc = FixtureLogChecker()
    logger.debug("test")
    flc.assert_not_info("test")


def test_negative_level_warning(logger):
    flc = FixtureLogChecker()
    logger.info("test")
    flc.assert_not_warning("test")


def test_negative_level_error(logger):
    flc = FixtureLogChecker()
    logger.info("test")
    flc.assert_not_error("test")


# -- Usage as a fixture!

def test_as_fixture(testdir, pytestconfig):
    """Make sure that our plugin works."""
    # create a temporary conftest.py file
    plugin_fpath = os.path.join(pytestconfig.rootdir, 'logassert', 'pytest_plugin.py')
    with open(plugin_fpath, 'rt', encoding='utf8') as fh:
        testdir.makeconftest(fh.read())

    # create a temporary pytest test file
    testdir.makepyfile(
        """
        def test_hello_default(logged):
            logged.assert_not_logged("anything")
    """
    )

    # run the test with pytest
    result = testdir.runpytest()

    # check that the test passed
    result.assert_outcomes(passed=1)
