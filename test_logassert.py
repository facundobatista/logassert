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

"""Tests for the main module."""

import logging
import unittest

import logassert


class FakeTestCase:
    """A fake to record if stuff failed."""
    def __init__(self):
        self.failed = None

    def fail(self, text):
        self.failed = text


class BasicUsageTestCase(unittest.TestCase):
    """Basic usage."""

    def test_simple_assert_ok(self):
        ftc = FakeTestCase()
        logger = logging.getLogger()
        logassert.setup(ftc, '')
        logger.debug("test")
        ftc.assertLogged("test")
        self.assertEqual(ftc.failed, None)

    def test_simple_assert_ok_with_replaces(self):
        ftc = FakeTestCase()
        logger = logging.getLogger()
        logassert.setup(ftc, '')
        logger.debug("test %d %r", 65, 'foobar')
        ftc.assertLogged("test", "65", "foobar")
        self.assertEqual(ftc.failed, None)

    def test_simple_assert_fail(self):
        ftc = FakeTestCase()
        logger = logging.getLogger()
        logassert.setup(ftc, '')
        logger.debug("test")
        ftc.assertLogged("test2")
        self.assertEqual(ftc.failed, "Tokens ('test2',) not found, all was logged is...\n"
                                     "    DEBUG     'test'")

    def test_simple_assert_fail_with_replaces(self):
        ftc = FakeTestCase()
        logger = logging.getLogger()
        logassert.setup(ftc, '')
        logger.debug("test %d %r", 65, 'foobar')
        ftc.assertLogged("test", "pumba")
        self.assertEqual(ftc.failed, "Tokens ('test', 'pumba') not found, all was logged is...\n"
                                     "    DEBUG     \"test 65 'foobar'\"")

    def test_assert_different_level_ok_debug(self):
        ftc = FakeTestCase()
        logger = logging.getLogger()
        logassert.setup(ftc, '')
        logger.debug("test")
        ftc.assertLoggedDebug("test")
        self.assertEqual(ftc.failed, None)

    def test_assert_different_level_ok_info(self):
        ftc = FakeTestCase()
        logger = logging.getLogger()
        logassert.setup(ftc, '')
        logger.info("test")
        ftc.assertLoggedInfo("test")
        self.assertEqual(ftc.failed, None)

    def test_assert_different_level_ok_error(self):
        ftc = FakeTestCase()
        logger = logging.getLogger()
        logassert.setup(ftc, '')
        logger.error("test")
        ftc.assertLoggedError("test")
        self.assertEqual(ftc.failed, None)

    def test_assert_different_level_ok_warning(self):
        ftc = FakeTestCase()
        logger = logging.getLogger()
        logassert.setup(ftc, '')
        logger.warning("test")
        ftc.assertLoggedWarning("test")
        self.assertEqual(ftc.failed, None)

    def test_assert_different_level_fail_oneway(self):
        ftc = FakeTestCase()
        logger = logging.getLogger()
        logassert.setup(ftc, '')
        logger.warning("test")
        ftc.assertLoggedDebug("test")
        self.assertEqual(ftc.failed, "Tokens ('test',) not found in DEBUG, all was logged is...\n"
                                     "    WARNING   'test'")

    def test_assert_different_level_fail_inverse(self):
        ftc = FakeTestCase()
        logger = logging.getLogger()
        logassert.setup(ftc, '')
        logger.debug("test")
        ftc.assertLoggedWarning("test")
        self.assertEqual(
            ftc.failed, "Tokens ('test',) not found in WARNING, all was logged is...\n"
                        "    DEBUG     'test'")
