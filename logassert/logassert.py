# Copyright 2015-2022 Facundo Batista
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

        # hook in the logger and set level
        self.logger = logger = logging.getLogger(log_path)
        self.original_logger_level = logger.level
        logger.setLevel(logging.DEBUG)

        # ensure there are not other _StoringHandlers
        logger.handlers[:] = [h for h in logger.handlers if not isinstance(h, _StoringHandler)]

        logger.addHandler(self)
        self.setLevel(logging.DEBUG)

        # hold a kind of record with the message already composed
        self.records = []

    def teardown(self):
        """Remove self from logger and set it up to the original level."""
        self.logger.handlers[:] = [
            h for h in self.logger.handlers if not isinstance(h, _StoringHandler)]
        self.logger.setLevel(self.original_logger_level)

    def reset(self):
        """Clean the stored records."""
        self.records.clear()

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
    default_response = None

    def __init__(self, token):
        self.token = token

    def search(self, message):
        """Search the token in the message, return if it's present."""
        raise NotImplementedError()

    def __str__(self):
        return "{} {!r} check".format(self.__class__.__name__.lower(), self.token)


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


class Sequence(Matcher):
    """A matcher that just holds its inners so each one can be verified separatedly.

    Note it doesn't define a `search` method, as it should never be called.
    """

    def __init__(self, *tokens):
        super().__init__(tokens)


class _Nothing(Matcher):
    """A matcher that is succesful only if nothing was logged."""
    default_response = True

    def search(self, message):
        """If a message was given, it implies "something was logged"."""
        # as a message happened, change the final default response
        self.default_response = None
        return False

    def __str__(self):
        return 'nothing'


NOTHING = _Nothing(None)


class PyTestComparer:
    def __init__(self, handler, level=None):
        self.handler = handler
        self.level = level
        self._matcher_description = ""

    def _get_matcher(self, item):
        """Produce a real matcher from a specific item."""
        if isinstance(item, str):
            # item is not specific, so default to Regex
            return Regex(item)
        if isinstance(item, Matcher):
            return item
        raise ValueError("Unknown item type: {!r}".format(item))

    def __contains__(self, item):
        if isinstance(item, Sequence):
            self._matcher_description = str(item)
            # sequence! all needs to succeed, in order
            results = []
            for subitem in item.token:
                matcher = self._get_matcher(subitem)
                result = self._check(matcher)
                if result is None:
                    # didn't succeed, calling it off
                    break
                else:
                    results.append(result)
            else:
                # all went fine... now check if it was in the proper order
                expected_sequence = list(range(results[0], len(item.token) + 1))
                if expected_sequence == results:
                    return True

        else:
            # simple matcher, check if it just succeeds
            matcher = self._get_matcher(item)
            self._matcher_description = str(matcher)
            if self._check(matcher) is not None:
                return True
        return False

    @property
    def messages(self):
        """Get all the messages in this log, to show when an assert fails."""
        if self.level is None:
            level_name = "any level"
        else:
            level_name = logging.getLevelName(self.level)
        records = self._get_records()
        if records:
            title = "for {} in {} failed; logged lines:".format(
                self._matcher_description, level_name)
        else:
            title = "for {} in {} failed; no logged lines at all!".format(
                self._matcher_description, level_name)

        messages = [title]
        for _, logged_levelname, logged_message in records:
            messages.append("     {:9s} {!r}".format(logged_levelname, logged_message))
        return messages

    def _get_records(self):
        """Get the level number, level name and message from the logged records."""
        return [(r.levelno, r.levelname, r.message.split('\n')[0]) for r in self.handler.records]

    def _check(self, matcher):
        """Check if the matcher is ok with any of the logged levels/messages."""
        for idx, (logged_level, _, logged_message) in enumerate(self._get_records()):
            if logged_level == self.level or self.level is None:
                if matcher.search(logged_message):
                    return idx
        return matcher.default_response


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
        if name in ('reset', 'teardown'):
            return getattr(handler, name)

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
