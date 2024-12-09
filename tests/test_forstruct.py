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

import pytest
import structlog

from logassert import Exact, Multiple, Sequence, NOTHING, Struct, CompleteStruct

logger = structlog.get_logger()


# -- Basic usage

def test_basic_simple_assert_ok_simple(logs):
    logger.debug("test")
    assert "test" in logs.any_level


def test_basic_simple_assert_ok_with_kwargs(logs):
    logger.debug("test", foo="65", extra="bar")
    assert Struct("test", foo="65", extra="bar") in logs.any_level


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


def test_safe_dict(logs):
    kwargs = {"baz": "123"}
    logger.debug("foobar", **kwargs)
    assert Struct("foobar", **kwargs) in logs.debug
    assert kwargs == {"baz": "123"}


# -- non-string fields

def test_nonstrings_basic(logs):
    logger.debug("test", foo=653, bar="653")
    assert Struct("test", foo=653, bar="653") in logs.any_level
    assert Struct("test", foo=653, bar="65") in logs.any_level
    assert Struct("test", foo=65, bar="653") not in logs.any_level


def test_nonstrings_none(logs):
    logger.debug("test", foo=None)
    assert Struct("test", foo=None) in logs.any_level
    assert Struct("test", foo="") not in logs.any_level


def test_nonstrings_other_matchers(logs):
    logger.debug("test", foo=None, bar=123)
    assert Struct("test", foo="", bar="123") not in logs.any_level
    assert Struct("test", foo=Exact(""), bar=Exact("123")) not in logs.any_level
    assert Struct("test", foo="", bar=Multiple("1", "2")) not in logs.any_level


# -- supports helpers also in "regular fixture" way

def test_compatibility_exact(logs):
    logger.debug("foo 42")
    assert Exact("foo 42") in logs.debug


def test_compatibility_multiple(logs):
    logger.debug("foo bar 42")
    assert Multiple("foo", "bar") in logs.debug


def test_compatibility_sequence(logs):
    logger.debug("a1")
    logger.debug("a2")
    assert Sequence("a1", "a2") in logs.debug


def test_compatibility_nothing(logs):
    logger.debug("aaa")
    assert NOTHING in logs.warning


# -- new Struct

def test_struct_justmessage_regex(logs):
    logger.debug("test")
    assert Struct("te.t") in logs.any_level

    comparer = logs.debug
    check_ok = comparer.__contains__(Struct("text"))
    assert not check_ok
    assert comparer.messages == [
        "for Struct('text') in DEBUG failed; logged lines:",
        "     DEBUG     'test'",
    ]


def test_struct_justmessage_exact(logs):
    logger.debug("test")
    assert Struct(Exact("test")) in logs.any_level

    comparer = logs.debug
    check_ok = comparer.__contains__(Struct(Exact("te.t")))
    assert not check_ok
    assert comparer.messages == [
        "for Struct(Exact('te.t')) in DEBUG failed; logged lines:",
        "     DEBUG     'test'",
    ]


def test_struct_justmessage_multiple(logs):
    logger.debug("test-foo!!!bar")
    assert Struct(Multiple("foo", "bar")) in logs.any_level

    comparer = logs.debug
    check_ok = comparer.__contains__(Struct(Multiple("foo", "xxx")))
    assert not check_ok
    assert comparer.messages == [
        "for Struct(Multiple('foo', 'xxx')) in DEBUG failed; logged lines:",
        "     DEBUG     'test-foo!!!bar'",
    ]


def test_struct_justmessage_sequence(logs):
    logger.debug("test1")
    logger.debug("test2")
    assert Sequence(Struct("test1"), Struct("test2")) in logs.any_level


def test_struct_kwargs_one_regex(logs):
    logger.debug("test", foo="bar")
    assert Struct("test", foo="ba.") in logs.any_level
    assert Struct("te.t", foo="bar") in logs.any_level


def test_struct_kwargs_one_exact(logs):
    logger.debug("test", foo="bar")
    assert Struct(Exact("test"), foo="bar") in logs.any_level

    comparer = logs.debug
    check_ok = comparer.__contains__(Struct(Exact("te.t"), foo="bar"))
    assert not check_ok
    assert comparer.messages == [
        "for Struct(Exact('te.t'), foo='bar') in DEBUG failed; logged lines:",
        "     DEBUG     'test' {'foo': 'bar'}",
    ]

    check_ok = comparer.__contains__(Struct("test", foo=Exact("ba.")))
    assert not check_ok
    assert comparer.messages == [
        "for Struct('test', foo=Exact('ba.')) in DEBUG failed; logged lines:",
        "     DEBUG     'test' {'foo': 'bar'}",
    ]


def test_struct_kwargs_one_ok_sequence(logs):
    logger.debug("test1", x="1")
    logger.debug("test2", y="2")
    assert Sequence(Struct("test1", x="1"), Struct("test2", y="2")) in logs.any_level


def test_struct_kwargs_one_fail(logs):
    logger.debug("test", foo="bar")
    assert Struct("tex!", foo="bar") not in logs.any_level
    assert Struct("test", foo="ba!") not in logs.any_level


def test_struct_kwargs_multiple_simple(logs):
    logger.debug("test", foo="aaa", bar="bbb", baz="ccc")
    assert Struct("test", foo="aaa", bar="bbb", baz="ccc") in logs.any_level
    assert Struct("test", foo="XXX", bar="bbb", baz="ccc") not in logs.any_level
    assert Struct("test", foo="aaa", bar="XXX", baz="ccc") not in logs.any_level
    assert Struct("test", foo="aaa", bar="bbb", baz="XXX") not in logs.any_level


def test_struct_kwargs_multiple_combinations(logs):
    logger.debug("test", foo="one field", bar="another field")
    assert Struct("test", foo="one.field", bar=Exact("another field")) in logs.any_level
    assert Struct("test", foo="one.field", bar=Exact("another.field")) not in logs.any_level


def test_struct_coverage_lessthan(logs):
    logger.debug("test", foo="aaa", bar="bbb", baz="ccc")
    assert Struct("test") in logs.any_level

    assert Struct("test", foo="aaa") in logs.any_level
    assert Struct("test", bar="bbb") in logs.any_level
    assert Struct("test", baz="ccc") in logs.any_level

    assert Struct("test", foo="aaa", bar="bbb") in logs.any_level
    assert Struct("test", foo="aaa", baz="ccc") in logs.any_level
    assert Struct("test", bar="bbb", baz="ccc") in logs.any_level


def test_struct_coverage_exact(logs):
    logger.debug("test")
    assert Struct("test") in logs.any_level

    logger.debug("test", foo="aaa")
    assert Struct("test", foo="aaa") in logs.any_level

    logger.debug("test", foo="aaa", bar="bbb")
    assert Struct("test", foo="aaa", bar="bbb") in logs.any_level


def test_struct_coverage_exceeded(logs):
    logger.debug("test")
    with pytest.raises(AssertionError):
        assert Struct("test", onetoomuch="bad") in logs.any_level

    logger.debug("test", foo="aaa")
    with pytest.raises(AssertionError):
        assert Struct("test", foo="aaa", onetoomuch="bad") in logs.any_level

    logger.debug("test", foo="aaa", bar="bbb")
    with pytest.raises(AssertionError):
        assert Struct("test", foo="aaa", bar="bbb", onetoomuch="bad") in logs.any_level


# -- cases for FullStruct


def test_completestruct_coverage_lessthan_justmesage(logs):
    logger.debug("test", foo="one field")
    assert CompleteStruct("test") not in logs.any_level


def test_completestruct_coverage_lessthan_kwargs(logs):
    logger.debug("test", foo="ok", bar="another field")
    assert CompleteStruct("test", foo="ok") not in logs.any_level


def test_completestruct_coverage_exact(logs):
    logger.debug("test")
    assert CompleteStruct("test") in logs.any_level
    logger.debug("test", foo="ok")
    assert CompleteStruct("test", foo="ok") in logs.any_level


def test_completestruct_coverage_exceeded(logs):
    logger.debug("test")
    assert CompleteStruct("test", extra="") not in logs.any_level
    logger.debug("test", foo="ok")
    assert CompleteStruct("test", foo="ok", extra="") not in logs.any_level


# -- integration tests


def test_with_factory_args(integtest_runner):
    """The logger is created passing some parameter."""
    result = integtest_runner(
        """
        import structlog

        import pytest

        from logassert import logassert

        logger = structlog.getLogger("somemod")  # typical __name__

        def test_1(logs):
            logger.debug('test')
            assert "test" in logs.any_level
    """
    )
    print('\n'.join(result.stdout.lines))

    # check that the test passed
    result.assert_outcomes(passed=1)
