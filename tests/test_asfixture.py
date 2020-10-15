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

"""Tests for the main module when used as a pytest fixture."""

import logging

import pytest

from logassert import Exact, Multiple

logger = logging.getLogger()


# -- Basic usage

def test_basic_simple_assert_ok_simple(logs):
    logger.debug("test")
    assert "test" in logs.any_level


def test_basic_simple_assert_ok_with_replaces(logs):
    logger.debug("test %d %r", 65, 'foobar')
    assert "test 65 'foobar'" in logs.any_level


def test_basic_simple_negated_assert_(logs):
    logger.debug("aaa")
    assert "aaa" not in logs.warning  # different than logged
    assert "bbb" not in logs.any_level  # checking other text in any level
    assert "bbb" not in logs.debug  # checking other text in same level


def test_failure_message_simple(logs):
    logger.debug("aaa")
    comparer = logs.debug
    check_ok = comparer.__contains__("bbb")
    assert not check_ok
    assert comparer.messages == [
        "for regex 'bbb' check in DEBUG failed; logged lines:",
        "     DEBUG     'aaa'",
    ]


def test_failure_message_multiple(logs):
    logger.debug("aaa")
    logger.warning("bbb")
    comparer = logs.debug
    check_ok = comparer.__contains__("bbb")
    assert not check_ok
    assert comparer.messages == [
        "for regex 'bbb' check in DEBUG failed; logged lines:",
        "     DEBUG     'aaa'",
        "     WARNING   'bbb'",
    ]


def test_failure_message_exception(logs):
    try:
        raise ValueError("test error")
    except ValueError:
        logger.exception("test message")

    comparer = logs.error
    check_ok = comparer.__contains__("will make it fail")
    assert not check_ok
    assert comparer.messages == [
        "for regex 'will make it fail' check in ERROR failed; logged lines:",
        "     ERROR     'test message'",
    ]


def test_regex_matching_exact(logs):
    logger.debug("foo 42")
    assert r"foo 42" in logs.debug
    assert r"foo \d\d" in logs.debug


def test_regex_matching_inside(logs):
    logger.debug("foo bar 42")
    assert r"bar \d\d" in logs.debug
    assert r"ba." in logs.debug
    assert r"f.. bar" in logs.debug
    with pytest.raises(AssertionError):
        assert r"foo 42" in logs.debug


def test_regex_matching_forcing_complete(logs):
    logger.debug("foo x bar")
    assert r"^foo . bar$" in logs.debug
    with pytest.raises(AssertionError):
        assert r"^foo .$" in logs.debug


def test_exact_cases(logs):
    logger.debug("foo 42")
    assert Exact("foo 42") in logs.debug
    assert Exact("foo ..") not in logs.debug
    assert Exact("foo") not in logs.debug


def test_exact_failure(logs):
    logger.debug("aaa")
    comparer = logs.debug
    check_ok = comparer.__contains__(Exact("bbb"))
    assert not check_ok
    assert comparer.messages == [
        "for exact 'bbb' check in DEBUG failed; logged lines:",
        "     DEBUG     'aaa'",
    ]


def test_multiple_cases(logs):
    logger.debug("foo bar 42")
    assert Multiple("foo bar 42") in logs.debug
    assert Multiple("foo bar 42", "extra") not in logs.debug
    assert Multiple("foo", "bar") in logs.debug
    assert Multiple("42", "bar") in logs.debug
    assert Multiple("foo 42") not in logs.debug
    assert Multiple("foo.*") not in logs.debug


def test_multiple_failure(logs):
    logger.debug("aaa")
    comparer = logs.debug
    check_ok = comparer.__contains__(Multiple("bbb", 'ccc'))
    assert not check_ok
    assert comparer.messages == [
        "for multiple ('bbb', 'ccc') check in DEBUG failed; logged lines:",
        "     DEBUG     'aaa'",
    ]


def test_basic_avoid_delayed_messaging(logs):
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
    assert r"feeling lucky\? didn't explode" in logs.debug


def test_reset(logs):
    logger.debug("foobar")
    assert "foobar" in logs.debug
    logs.reset()
    assert "foobar" not in logs.debug


# -- Levels

def test_levels_assert_ok_debug(logs):
    logger.debug("test")
    assert "test" in logs.debug


def test_levels_assert_ok_info(logs):
    logger.info("test")
    assert "test" in logs.info


def test_levels_assert_ok_warning(logs):
    logger.warning("test")
    assert "test" in logs.warning


def test_levels_assert_ok_error(logs):
    logger.error("test")
    assert "test" in logs.error


def test_levels_assert_ok_exception(logs):
    try:
        raise ValueError("test error")
    except ValueError:
        logger.exception("test message")
    assert "^test message$" in logs.error


def test_levels_assert_different_level_fail_debug_warning(logs):
    logger.warning("test")
    with pytest.raises(AssertionError):
        assert "test" in logs.debug


def test_levels_assert_different_level_fail_warning_debug(logs):
    logger.debug("test")
    with pytest.raises(AssertionError):
        assert "test" in logs.warning


# -- Usage as a fixture!

def test_as_fixture_basic(testdir, pytestconfig):
    """Make sure that our plugin works."""
    # create a temporary conftest.py file
    plugin_fpath = pytestconfig.rootdir / 'logassert' / 'pytest_plugin.py'
    with plugin_fpath.open('rt', encoding='utf8') as fh:
        testdir.makeconftest(fh.read())

    # create a temporary pytest test file
    testdir.makepyfile(
        """
        def test_hello_default(logs):
            assert "anything" not in logs.any_level
    """
    )

    # run the test with pytest
    result = testdir.runpytest()

    # check that the test passed
    result.assert_outcomes(passed=1)


def test_as_fixture_double_handler(testdir, pytestconfig):
    """Check that we don't hook many handlers."""
    # create a temporary conftest.py file
    plugin_fpath = pytestconfig.rootdir / 'logassert' / 'pytest_plugin.py'
    with plugin_fpath.open('rt', encoding='utf8') as fh:
        testdir.makeconftest(fh.read())

    # create a temporary pytest test file
    testdir.makepyfile(
        """
        from logassert import logassert

        import logging

        logger = logging.getLogger()

        def test_1(logs):
            logger.debug('test')
            assert "test" in logs.any_level

        def test_2(logs):
            logger.debug('test')
            assert "test" in logs.debug
            assert len(
                [h for h in logger.handlers if isinstance(h, logassert._StoringHandler)]) == 1
    """
    )

    # run the test with pytest
    result = testdir.runpytest()
    print('\n'.join(result.stdout.lines))

    # check that the test passed
    result.assert_outcomes(passed=2)


def test_as_fixture_no_record_leaking(testdir, pytestconfig):
    """Nothing is leaked between tests."""
    # create a temporary conftest.py file
    plugin_fpath = pytestconfig.rootdir / 'logassert' / 'pytest_plugin.py'
    with plugin_fpath.open('rt', encoding='utf8') as fh:
        testdir.makeconftest(fh.read())

    # create a temporary pytest test file
    testdir.makepyfile(
        """
        import logging

        logger = logging.getLogger()

        def test_1(logs):
            logger.debug('test')
            assert "test" in logs.any_level

        def test_2(logs):
            assert "test" not in logs.any_level
    """
    )

    # run the test with pytest
    result = testdir.runpytest()

    # check that the test passed
    result.assert_outcomes(passed=2)


def test_lgged_lines_are_shown_when_unsing_not_in(logs):
    logger.error("foo")
    with pytest.raises(AssertionError) as err:
        assert "foo" not in logs.error

    expected_log = ("assert for regex 'foo' check in ERROR failed; logged lines:\n"
                    "       ERROR     'foo'")

    assert expected_log == str(err.value)
