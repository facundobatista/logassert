# Copyright 2015-2020 Facundo Batista
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

"""Main module."""

import collections
import functools
import logging.handlers

Record = collections.namedtuple("Record", "levelname levelno message")


class _BaseLogChecker(logging.handlers.MemoryHandler):
    """A fake handler to store the records."""

    def __init__(self, log_path):
        # init memory handler to never flush
        super().__init__(capacity=100000, flushLevel=1000)

        # hook in the logger
        logger = logging.getLogger(log_path)
        logger.addHandler(self)
        logger.setLevel(logging.DEBUG)
        self.setLevel(logging.DEBUG)

        # hold a kind of record with the message already composed
        self.records = []

    def emit(self, record):
        """Store the message, not only the record.

        Here is where we get in the middle of the logging machinery to capture messages.
        """
        r = Record(levelno=record.levelno, levelname=record.levelname, message=self.format(record))
        self.records.append(r)
        return super().emit(record)

    def _check_generic_pos(self, *tokens):
        """Check if the different tokens were logged in one record, any level."""
        for record in self.records:
            if all(token in record.message for token in tokens):
                return

        # didn't exit, all tokens are not present in the same record
        msgs = ["Tokens {} not found, all was logged is...".format(tokens)]
        for record in self.records:
            msgs.append("    {:9s} {!r}".format(record.levelname, record.message))
        self.fail("\n".join(msgs))

    def _check_pos(self, level, *tokens):
        """Check if the different tokens were logged in one record, assert by level."""
        for record in self.records:
            if all(record.levelno == level and token in record.message for token in tokens):
                return

        # didn't exit, all tokens are not present in the same record
        level_name = logging.getLevelName(level)
        msgs = ["Tokens {} not found in {}, all was logged is...".format(tokens, level_name)]
        for record in self.records:
            msgs.append("    {:9s} {!r}".format(record.levelname, record.message))
        self.fail("\n".join(msgs))

    def _check_neg(self, level, *tokens):
        """Check that the different tokens were NOT logged in one record, assert by level."""
        for record in self.records:
            if level is not None and record.levelno != level:
                continue
            if all(token in record.message for token in tokens):
                break
        else:
            return

        # didn't exit, all tokens found in the same record
        msg = "Tokens {} found in the following record:  {}  {!r}".format(
            tokens, record.levelname, record.message)
        self.fail(msg)


class SetupLogChecker(_BaseLogChecker):
    """A version of the LogChecker to use in classic TestCases."""

    def __init__(self, test_instance, log_path):
        super().__init__(log_path)

        # fix TestCase instance with all classic-looking helpers
        self.test_instance = test_instance
        test_instance.assertLogged = self._check_generic_pos
        test_instance.assertLoggedError = functools.partial(self._check_pos, logging.ERROR)
        test_instance.assertLoggedWarning = functools.partial(self._check_pos, logging.WARNING)
        test_instance.assertLoggedInfo = functools.partial(self._check_pos, logging.INFO)
        test_instance.assertLoggedDebug = functools.partial(self._check_pos, logging.DEBUG)
        test_instance.assertNotLogged = functools.partial(self._check_neg, None)
        test_instance.assertNotLoggedError = functools.partial(self._check_neg, logging.ERROR)
        test_instance.assertNotLoggedWarning = functools.partial(self._check_neg, logging.WARNING)
        test_instance.assertNotLoggedInfo = functools.partial(self._check_neg, logging.INFO)
        test_instance.assertNotLoggedDebug = functools.partial(self._check_neg, logging.DEBUG)

    def fail(self, message):
        """Called on failure."""
        self.test_instance.fail(message)


class FixtureLogChecker(_BaseLogChecker):
    """A version of the LogChecker to use as a pytest fixture."""

    def __init__(self, log_path=''):
        super().__init__(log_path)

        self.assert_logged = self._check_generic_pos
        self.assert_error = functools.partial(self._check_pos, logging.ERROR)
        self.assert_warning = functools.partial(self._check_pos, logging.WARNING)
        self.assert_info = functools.partial(self._check_pos, logging.INFO)
        self.assert_debug = functools.partial(self._check_pos, logging.DEBUG)
        self.assert_not_logged = functools.partial(self._check_neg, None)
        self.assert_not_error = functools.partial(self._check_neg, logging.ERROR)
        self.assert_not_warning = functools.partial(self._check_neg, logging.WARNING)
        self.assert_not_info = functools.partial(self._check_neg, logging.INFO)
        self.assert_not_debug = functools.partial(self._check_neg, logging.DEBUG)

    def fail(self, message):
        """Called on failure."""
        raise AssertionError(message)


def setup(test_instance, logger_name):
    """Set up the log monitoring.

    The test instance is the one where this will be used. The logger name is
    the one of the logger to supervise.

    Example of use for classic tests (for "pytest" just install it and will be a fixture 'logged'):

        class MyTestCase(unittest.TestCase):
            def setUp(self):
                logassert.setup(self, 'mylogger')

            def test_blah(self):
                (...)
                self.assertLogged(...)
    """
    return SetupLogChecker(test_instance, logger_name)
