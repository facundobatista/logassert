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

    def setUp(self):
        self.logger = logging.getLogger()
        self.logger.handlers = []

    def test_simple_assert_ok(self):
        ftc = FakeTestCase()
        logassert.setup(ftc, '')
        self.logger.debug("test")
        ftc.assertLogged("test")
        self.assertEqual(ftc.failed, None)

    def test_simple_assert_ok_extras(self):
        ftc = FakeTestCase()
        logassert.setup(ftc, '')
        formatter = logging.Formatter("%(message)s %(foo)s")
        for h in self.logger.handlers:
            h.setFormatter(formatter)
        self.logger.debug("test", extra={'foo': 'bar'})
        ftc.assertLogged("test bar")
        self.assertEqual(ftc.failed, None)

    def test_simple_assert_ok_with_replaces(self):
        ftc = FakeTestCase()
        logassert.setup(ftc, '')
        self.logger.debug("test %d %r", 65, 'foobar')
        ftc.assertLogged("test", "65", "foobar")
        self.assertEqual(ftc.failed, None)

    def test_simple_assert_fail(self):
        ftc = FakeTestCase()
        logassert.setup(ftc, '')
        self.logger.debug("test")
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

    def test_avoid_delayed_messaging(self):
        ftc = FakeTestCase()
        logger = logging.getLogger()
        logassert.setup(ftc, '')

        class Exploding:
            """Explode on delayed str."""
            should_explode = False

            def __str__(self):
                if self.should_explode:
                    raise ValueError("str exploded")
                return "didn't explode"

        # log something using the Exploding class
        exploding = Exploding()
        logger.debug("feeling lucky? %s", exploding)

        # now flag the class to explode and check
        exploding.should_explode = True
        ftc.assertLogged("feeling lucky", "didn't explode")


class LevelsTestCase(unittest.TestCase):
    """Work aware of logging levels."""

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

    def test_assert_different_level_ok_exception(self):
        ftc = FakeTestCase()
        logger = logging.getLogger()
        logassert.setup(ftc, '')
        try:
            raise ValueError("test error")
        except:
            logger.exception("test message")
        ftc.assertLoggedError("test error")
        ftc.assertLoggedError("test message")
        ftc.assertLoggedError("ValueError")
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


class NotLoggedTestCase(unittest.TestCase):
    """Also check that it wasn't logged."""

    def test_simple_ok(self):
        ftc = FakeTestCase()
        logger = logging.getLogger()
        logassert.setup(ftc, '')
        logger.debug("test")
        ftc.assertNotLogged("other")
        self.assertEqual(ftc.failed, None)

    def test_simple_fail(self):
        ftc = FakeTestCase()
        logger = logging.getLogger()
        logassert.setup(ftc, '')
        logger.info("test")
        ftc.assertNotLogged("test")
        self.assertEqual(ftc.failed,
                         "Tokens ('test',) found in the following record:  INFO  'test'")

    def test_level_debug_ok(self):
        ftc = FakeTestCase()
        logger = logging.getLogger()
        logassert.setup(ftc, '')
        logger.info("test")
        ftc.assertNotLoggedDebug("test")
        self.assertEqual(ftc.failed, None)

    def test_level_debug_fail(self):
        ftc = FakeTestCase()
        logger = logging.getLogger()
        logassert.setup(ftc, '')
        logger.debug("test")
        ftc.assertNotLoggedDebug("test")
        self.assertEqual(ftc.failed,
                         "Tokens ('test',) found in the following record:  DEBUG  'test'")

    def test_level_info(self):
        ftc = FakeTestCase()
        logger = logging.getLogger()
        logassert.setup(ftc, '')
        logger.debug("test")
        ftc.assertNotLoggedInfo("test")
        self.assertEqual(ftc.failed, None)

    def test_level_warning(self):
        ftc = FakeTestCase()
        logger = logging.getLogger()
        logassert.setup(ftc, '')
        logger.info("test")
        ftc.assertNotLoggedWarning("test")
        self.assertEqual(ftc.failed, None)

    def test_level_error(self):
        ftc = FakeTestCase()
        logger = logging.getLogger()
        logassert.setup(ftc, '')
        logger.info("test")
        ftc.assertNotLoggedError("test")
        self.assertEqual(ftc.failed, None)
