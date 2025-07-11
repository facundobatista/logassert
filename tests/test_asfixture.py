# Copyright 2020-2025 Facundo Batista
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

from logassert import Exact, Multiple, Sequence, NOTHING, Struct, CompleteStruct

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


def test_reset(logs):
    logger.debug("foobar")
    assert "foobar" in logs.debug
    logs.reset()
    assert "foobar" not in logs.debug


# -- messages

def test_failure_message_simple(logs):
    logger.debug("aaa")
    with pytest.raises(AssertionError) as err:
        assert "bbb" in logs.debug
    assert str(err.value) == (
        "assert for Regex('bbb') in DEBUG failed; logged lines:\n"
        "       DEBUG     'aaa'"
    )


def test_failure_message_no_logs(logs):
    with pytest.raises(AssertionError) as err:
        assert "bbb" in logs.debug
    assert str(err.value) == (
        "assert for Regex('bbb') in DEBUG failed; no logged lines at all!"
    )


def test_failure_message_any_level(logs):
    logger.debug("aaa")
    with pytest.raises(AssertionError) as err:
        assert "bbb" in logs.any_level
    assert str(err.value) == (
        "assert for Regex('bbb') in any level failed; logged lines:\n"
        "       DEBUG     'aaa'"
    )


def test_failure_message_multiple(logs):
    logger.debug("aaa")
    logger.warning("bbb")
    with pytest.raises(AssertionError) as err:
        assert "bbb" in logs.debug
    assert str(err.value) == (
        "assert for Regex('bbb') in DEBUG failed; logged lines:\n"
        "       DEBUG     'aaa'\n"
        "       WARNING   'bbb'"
    )


def test_failure_message_exception(logs):
    try:
        raise ValueError("test error")
    except ValueError:
        logger.exception("test message")

    with pytest.raises(AssertionError) as err:
        assert "will make it fail" in logs.error
    msg_lines = str(err.value).split("\n")
    assert msg_lines[0] == (
        "assert for Regex('will make it fail') in ERROR failed; logged lines:"
    )
    assert msg_lines[1].startswith(r"       ERROR     'test message\nTraceback (most recent")


# -- different forms of comparison

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
        "for Exact('bbb') in DEBUG failed; logged lines:",
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
        "for Multiple('bbb', 'ccc') in DEBUG failed; logged lines:",
        "     DEBUG     'aaa'",
    ]


def test_sequence_simple(logs):
    logger.debug("foo")
    logger.debug("a1")
    logger.debug("a2")
    logger.debug("bar")
    assert Sequence("a1", "a2") in logs.debug


def test_sequence_multiple_matches_simple(logs):
    # kindly provided by Benjamin Desef in https://github.com/facundobatista/logassert/issues/18
    logger.info("event A")
    logger.info("event B")
    logger.info("event A")
    assert Sequence("event A", "event B", "event A") in logs.info


def test_sequence_multiple_matches_misleading_first(logs):
    logger.info("foo")
    logger.info("a1")  # sequence may start here but not really
    logger.info("bar")
    logger.info("a1")
    logger.info("a2")
    logger.info("a1")
    assert Sequence("a1", "a2", "a1") in logs.info


def test_sequence_rotated(logs):
    logger.debug("a2")
    logger.debug("a1")
    comparer = logs.debug
    check_ok = comparer.__contains__(Sequence("a1", "a2"))
    assert not check_ok
    assert comparer.messages == [
        "for Sequence('a1', 'a2') in DEBUG failed; logged lines:",
        "     DEBUG     'a2'",
        "     DEBUG     'a1'",
    ]


def test_sequence_partial(logs):
    logger.debug("a1")
    comparer = logs.debug
    check_ok = comparer.__contains__(Sequence("a1", "a2"))
    assert not check_ok
    assert comparer.messages == [
        "for Sequence('a1', 'a2') in DEBUG failed; logged lines:",
        "     DEBUG     'a1'",
    ]


def test_sequence_interrupted_same_level(logs):
    logger.debug("a1")
    logger.debug("--")
    logger.debug("a2")
    comparer = logs.debug
    check_ok = comparer.__contains__(Sequence("a1", "a2"))
    assert not check_ok
    assert comparer.messages == [
        "for Sequence('a1', 'a2') in DEBUG failed; logged lines:",
        "     DEBUG     'a1'",
        "     DEBUG     '--'",
        "     DEBUG     'a2'",
    ]


def test_sequence_interrupted_different_level_check_specific_level(logs):
    # kindly provided by Benjamin Desef in https://github.com/facundobatista/logassert/issues/18
    logger.debug("a1")
    logger.info("--")
    logger.debug("a2")
    # the "interruption" is in other level, not the checked one, so it does not really interrupt
    assert Sequence("a1", "a2") in logs.debug


def test_sequence_interrupted_different_level_check_any_level(logs):
    logger.debug("a1")
    logger.info("--")
    logger.debug("a2")
    comparer = logs.any_level
    check_ok = comparer.__contains__(Sequence("a1", "a2"))
    assert not check_ok
    assert comparer.messages == [
        "for Sequence('a1', 'a2') in any level failed; logged lines:",
        "     DEBUG     'a1'",
        "     INFO      '--'",
        "     DEBUG     'a2'",
    ]


def test_sequence_inners(logs):
    logger.debug("foo")
    logger.debug("xxx a1")
    logger.debug("xxx a2")
    logger.debug("xxx a3")
    logger.debug("bar")
    assert Sequence(
        ".* a.",
        Exact("xxx a2"),
        Multiple("a3", "xxx"),
    ) in logs.debug


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


def test_nothing_ok(logs):
    logger.debug("aaa")
    assert NOTHING in logs.warning


def test_nothing_repeated_crossed(logs):
    logger.debug("aaa")
    with pytest.raises(AssertionError):
        assert NOTHING in logs.debug
    assert NOTHING in logs.warning


def test_nothing_fail_level(logs):
    logger.debug("aaa")
    with pytest.raises(AssertionError) as err:
        assert NOTHING in logs.debug
    assert str(err.value) == (
        "assert for nothing in DEBUG failed; logged lines:\n"
        "       DEBUG     'aaa'"
    )


def test_nothing_fail_any(logs):
    logger.debug("aaa")
    with pytest.raises(AssertionError) as err:
        assert NOTHING in logs.any_level
    assert str(err.value) == (
        "assert for nothing in any level failed; logged lines:\n"
        "       DEBUG     'aaa'"
    )


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
    assert "test.message" in logs.error
    assert "ValueError" in logs.error
    assert "test.error" in logs.error


def test_levels_assert_different_level_fail_debug_warning(logs):
    logger.warning("test")
    with pytest.raises(AssertionError):
        assert "test" in logs.debug


def test_levels_assert_different_level_fail_warning_debug(logs):
    logger.debug("test")
    with pytest.raises(AssertionError):
        assert "test" in logs.warning


# -- Usage as a fixture!

def test_as_fixture_basic(integtest_runner):
    """Make sure that our plugin works."""
    result = integtest_runner(
        """
        def test_hello_default(logs):
            assert "anything" not in logs.any_level
    """
    )

    # check that the test passed
    result.assert_outcomes(passed=1)


def test_as_fixture_double_handler(integtest_runner):
    """Check that we don't hook many handlers."""
    result = integtest_runner(
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
            hdlrs = [h for h in logger.handlers if isinstance(h, logassert._StdlibStoringHandler)]
            assert len(hdlrs) == 1
    """
    )
    print('\n'.join(result.stdout.lines))

    # check that the test passed
    result.assert_outcomes(passed=2)


def test_as_fixture_clean_up(integtest_runner):
    """Don't leave traces of setup."""
    result = integtest_runner(
        """
        import logging

        import pytest

        from logassert import logassert

        logger = logging.getLogger('')
        logger.setLevel(30)

        def test_1(logs):
            logger.debug('test')
            assert "test" in logs.any_level

        @pytest.fixture(scope="session", autouse=True)
        def cleanup(request):
            assert logger.getEffectiveLevel() == 30
            hdlrs = [h for h in logger.handlers if isinstance(h, logassert._StdlibStoringHandler)]
            assert len(hdlrs) == 0
    """
    )
    print('\n'.join(result.stdout.lines))

    # check that the test passed
    result.assert_outcomes(passed=1)


def test_as_fixture_no_record_leaking(integtest_runner):
    """Nothing is leaked between tests."""
    result = integtest_runner(
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
    # check that the test passed
    result.assert_outcomes(passed=2)


def test_logged_lines_are_shown_when_using_not_in(logs):
    logger.error("foo")
    with pytest.raises(AssertionError) as err:
        assert "foo" not in logs.error

    expected_log = ("assert for Regex('foo') in ERROR failed; logged lines:\n"
                    "       ERROR     'foo'")

    assert expected_log == str(err.value)


# -- clashing with other ways of using logassert

@pytest.mark.parametrize("struct_class", [Struct, CompleteStruct])
def test_struct(logs, struct_class):
    """Using struct without keywords is similar to not using it, just for flexibility."""
    logger.error("foo")
    assert struct_class("fo.") in logs.error
    assert struct_class("foo", bar=2) not in logs.error
