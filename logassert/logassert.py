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
import re

Record = collections.namedtuple("Record", "levelname levelno message")


class _StoringHandler(logging.handlers.MemoryHandler):
    """A fake handler to store the records."""

    def __init__(self, log_path):
        # init memory handler to never flush
        super().__init__(capacity=100000, flushLevel=1000)

        # hook in the logger
        logger = logging.getLogger(log_path)

        # ensure there are not other _StoringHandlers
        logger.handlers[:] = [h for h in logger.handlers if not isinstance(h, _StoringHandler)]

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


class SetupLogChecker:
    """A version of the LogChecker to use in classic TestCases."""

    def __init__(self, test_instance, log_path):
        self._log_checker = _StoringHandler(log_path)

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

    def _check_generic_pos(self, *tokens):
        """Check if the different tokens were logged in one record, any level."""
        for record in self._log_checker.records:
            if all(token in record.message for token in tokens):
                return

        # didn't exit, all tokens are not present in the same record
        msgs = ["Tokens {} not found, all was logged is...".format(tokens)]
        for record in self._log_checker.records:
            msgs.append("    {:9s} {!r}".format(record.levelname, record.message))
        self.test_instance.fail("\n".join(msgs))

    def _check_pos(self, level, *tokens):
        """Check if the different tokens were logged in one record, assert by level."""
        for record in self._log_checker.records:
            if all(record.levelno == level and token in record.message for token in tokens):
                return

        # didn't exit, all tokens are not present in the same record
        level_name = logging.getLevelName(level)
        msgs = ["Tokens {} not found in {}, all was logged is...".format(tokens, level_name)]
        for record in self._log_checker.records:
            msgs.append("    {:9s} {!r}".format(record.levelname, record.message))
        self.test_instance.fail("\n".join(msgs))

    def _check_neg(self, level, *tokens):
        """Check that the different tokens were NOT logged in one record, assert by level."""
        for record in self._log_checker.records:
            if level is not None and record.levelno != level:
                continue
            if all(token in record.message for token in tokens):
                break
        else:
            return

        # didn't exit, all tokens found in the same record
        msg = "Tokens {} found in the following record:  {}  {!r}".format(
            tokens, record.levelname, record.message)
        self.test_instance.fail(msg)


class Matcher:
    """A generic matcher."""
    def __init__(self, token):
        self.token = token

    def search(self, message):
        """Search the token in the message, return if it's present."""
        raise NotImplementedError()

    def __str__(self):
        return "{} {!r}".format(self.__class__.__name__.lower(), self.token)


class Regex(Matcher):
    """A matcher that uses the token string as a regex."""
    def __init__(self, token):
        super().__init__(token)
        self.regex = re.compile(token)

    def search(self, message):
        """Search the token in the message, return if it's present."""
        return bool(self.regex.search(message))


class Exact(Matcher):
    """A matcher that matches exactly the token string."""

    def search(self, message):
        """Search the token in the message, return if it's present."""
        return self.token == message


class Multiple(Matcher):
    """A matcher that matches multiple tokens (legacy support)."""

    def __init__(self, *tokens):
        super().__init__(tokens)

    def search(self, message):
        """Search the token in the message, return if it's present."""
        return all(t in message for t in self.token)


class PyTestComparer:
    def __init__(self, handler, level=None):
        self.handler = handler
        self.level = level
        self.messages = None

    def __contains__(self, item):
        # item is not specific, so default to Regex
        if isinstance(item, str):
            matcher = Regex(item)
        elif isinstance(item, Matcher):
            matcher = item
        else:
            raise ValueError("Unknown item type: {!r}".format(item))

        # check and store any given messages to be used when pytest asks for them at the moment
        # of showing the information to the user
        self.messages = self._check(matcher, self.level)

        # if have messages, return False to pytest so it flags the test as "failed"
        return not self.messages

    def _check(self, matcher, level):
        """Check if the regex applies to one logged record."""
        # get the messages with corresponding levels
        logged_records = [
            (r.levelno, r.levelname, r.message.split('\n')[0]) for r in self.handler.records]

        # verify if the matcher is ok with any of the logged levels/messages
        for logged_level, _, logged_message in logged_records:
            if logged_level == level or level is None:
                if matcher.search(logged_message):
                    return

        # didn't match any of the records, so prepare the resulting messages
        level_name = logging.getLevelName(level)
        msgs = ["for {} check in {} failed; logged lines:".format(matcher, level_name)]
        for _, logged_levelname, logged_message in logged_records:
            msgs.append("     {:9s} {!r}".format(logged_levelname, logged_message))
        return msgs


class FixtureLogChecker:
    """A version of the LogChecker to use as a pytest fixture."""

    # translation between the attributes and logging levels
    _levels = {
        'any_level': None,
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
    }

    def __init__(self):
        self.handler = _StoringHandler('')

    def __getattribute__(self, name):
        handler = object.__getattribute__(self, 'handler')
        if name == 'reset':
            return handler.records.clear

        # this is handled dinamically so we don't need to create a bunch of PyTestComparares
        # for every test, specially because most of them won't be used in that test
        _levels = object.__getattribute__(self, '_levels')
        try:
            level = _levels[name]
        except KeyError:
            raise AttributeError("'FixtureLogChecker' object has no attribute {!r}".format(name))

        return PyTestComparer(handler, level)


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
