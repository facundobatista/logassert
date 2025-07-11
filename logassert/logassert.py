# Copyright 2015-2025 Facundo Batista
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

import functools
import logging.handlers
import re

try:
    import structlog
except ImportError:
    # no structlog library present
    structlog = None

MISSING_MARK = object()


class SimpleRecord:
    """A record with simply level name and number, and just a string message."""

    def __init__(self, *, levelname, levelno, message):
        self.levelname = levelname
        self.levelno = levelno
        self.message = message
        self.extra_fields = {}

    @property
    def repr_content(self):
        """Representation of the content to show in messages."""
        return repr(self.message)

    def __str__(self):
        return f"<SimpleRecord [{self.levelname}] {self.message!r}>"


class StructRecord:
    """A record with level name and number, and info structured in different fields."""

    def __init__(self, *, levelname, levelno, event_dict):
        self.levelname = levelname
        self.levelno = levelno

        # copy to not risk modifying an object the user/structlog relies on, and prepare info
        data = event_dict.copy()
        self.message = data.pop("event")
        self.extra_fields = data

    @property
    def repr_content(self):
        """Representation of the content to show in messages."""
        result = repr(self.message)
        if self.extra_fields:
            result += f" {self.extra_fields}"
        return result

    def __str__(self):
        return f"<StructRecord [{self.levelname}] {self.message!r} {self.extra_fields}>"


class _StdlibStoringHandler(logging.handlers.MemoryHandler):
    """A fake handler to store the records."""

    def __init__(self, log_path):
        # init memory handler to never flush
        super().__init__(capacity=100000, flushLevel=1000)

        # hook in the logger and set level
        self.logger = logger = logging.getLogger(log_path)
        self.original_logger_level = logger.level
        logger.setLevel(logging.DEBUG)

        # ensure there are not other _StoringHandlers
        logger.handlers[:] = [
            h for h in logger.handlers if not isinstance(h, _StdlibStoringHandler)
        ]

        logger.addHandler(self)
        self.setLevel(logging.DEBUG)

        # hold a kind of record with the message already composed
        self.records = []

    def teardown(self):
        """Remove self from logger and set it up to the original level."""
        self.logger.handlers[:] = [
            h for h in self.logger.handlers if not isinstance(h, _StdlibStoringHandler)]
        self.logger.setLevel(self.original_logger_level)

    def reset(self):
        """Clean the stored records."""
        self.records.clear()

    def emit(self, record):
        """Store the message, not only the record.

        Here is where we get in the middle of the logging machinery to capture messages.
        """
        r = SimpleRecord(
            levelno=record.levelno,
            levelname=record.levelname,
            message=self.format(record),
        )
        self.records.append(r)
        return super().emit(record)


class _StructlogCapturer:
    """A layer above structlog functionality to store the records."""

    def __init__(self):
        # the factory receives the args (not kwargs) passed to `getLogger` call -- we're not
        # really using them, so we ignore them
        structlog.configure(logger_factory=lambda *args: self, processors=[self._capture])
        self.records = []

    def teardown(self):
        """Noop for structlog."""

    def reset(self):
        """Clean the stored records."""
        self.records.clear()

    def _capture(self, logger, levelname, event_dict):
        """Capture the info from structlog."""
        levelno = getattr(logging, levelname.upper())
        r = StructRecord(levelno=levelno, levelname=levelname, event_dict=event_dict)
        self.records.append(r)
        return event_dict

    def __getattr__(self, name):
        """Really return current interface and fake debug/info/error calls to do nothing."""
        if name in ("teardown", "reset"):
            return object.__getattr__(self, name)

        return lambda *args, **kwargs: None


class SetupLogChecker:
    """A version of the LogChecker to use in classic TestCases."""

    def __init__(self, test_instance, log_path):
        self._log_checker = _StdlibStoringHandler(log_path)

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
    default_response = False

    def __init__(self, token):
        self.token = token

    def _search(self, message):
        """Search the token in the message, return if it's present."""
        raise NotImplementedError()

    def search(self, *, record=None, message=MISSING_MARK):
        """Search the token in the record/message, return if it's present."""
        if message is MISSING_MARK:
            message = record.message

        # only support searching into non-strings if it's Exact; the rest relies
        # on searching in strings
        if not isinstance(self, Exact) and not isinstance(message, (str, bytes)):
            return False

        return self._search(message)

    def __str__(self):
        return f"{self.__class__.__name__}({self.token!r})"

    __repr__ = __str__


class Struct(Matcher):
    """A matcher that checks message and keyword arguments."""
    def __init__(self, token, **fields):
        super().__init__(token)
        self.fields = fields

    def _extra_fields_ok(self, record):
        """Validate needed extra fields are present."""
        return set(record.extra_fields).issuperset(self.fields)

    def search(self, record):
        """Search in message and possible fields, considering each case its own matcher."""
        if not self._extra_fields_ok(record):
            return False

        matcher = _get_matcher(self.token)
        if not matcher.search(message=record.message):
            return False

        for key, value in self.fields.items():
            matcher = _get_matcher(value)
            record_value = record.extra_fields.get(key, MISSING_MARK)
            if record_value is MISSING_MARK:
                continue

            if not matcher.search(message=record_value):
                return False

        return True

    def __str__(self):
        if self.fields:
            extra_fields = ", " + ", ".join(
                f"{key}={value!r}" for key, value in self.fields.items()
            )
        else:
            extra_fields = ""
        return f"{self.__class__.__name__}({self.token!r}{extra_fields})"


class CompleteStruct(Struct):
    """A variation of struct that checks that fields coverage is complete."""

    def _extra_fields_ok(self, record):
        """Validate extra fields matches on what was logged."""
        return set(record.extra_fields) == set(self.fields)


class Regex(Matcher):
    """A matcher that uses the token string as a regex."""
    def __init__(self, token):
        super().__init__(token)
        self.regex = re.compile(token)

    def _search(self, message):
        """Search the token in the message, return if it's present."""
        return bool(self.regex.search(message))


class Exact(Matcher):
    """A matcher that matches exactly the token string."""

    def _search(self, message):
        """Search the token in the message, return if it's present."""
        return self.token == message


class Multiple(Matcher):
    """A matcher that matches multiple tokens (legacy support)."""

    def __init__(self, *tokens):
        super().__init__(tokens)

    def _search(self, message):
        """Search the token in the message, return if it's present."""
        return all(t in message for t in self.token)

    def __str__(self):
        return f"{self.__class__.__name__}{self.token!r}"  # no extra parentheses over the tuple's

    __repr__ = __str__


class Sequence(Matcher):
    """A matcher that just holds its inners so each one can be verified separatedly.

    Note it doesn't define a `search` method, as it should never be called.
    """

    def __init__(self, *tokens):
        super().__init__(tokens)

    def __str__(self):
        return f"{self.__class__.__name__}{self.token!r}"  # no extra parentheses over the tuple's

    __repr__ = __str__


class _Nothing(Matcher):
    """A matcher that is succesful only if nothing was logged."""
    def __init__(self):
        super().__init__(None)  # no token!
        self.default_response = True

    def search(self, record):
        """If a record was given, it implies "something was logged"."""
        # as a message happened, change the final default response
        self.default_response = False
        return False

    def reset(self):
        """Change to initial status."""
        self.default_response = True

    def __str__(self):
        return 'nothing'


NOTHING = _Nothing()


def _get_matcher(item):
    """Produce a real matcher from a specific item."""
    if isinstance(item, (str, bytes)):
        # item is not specific, so default to Regex
        return Regex(item)
    if isinstance(item, Matcher):
        return item

    # any other type should match exactly -- this is to suppor when non-string is
    # matched to something else
    return Exact(item)


class PyTestComparer:
    def __init__(self, handlers, level=None):
        self.level = level
        self._matcher_description = ""
        self.records = self._get_records(handlers)

        # we need to reset the NOTHING comparer here so it's not polluted from the past
        NOTHING.reset()

    def __contains__(self, item):
        # get the records that apply for the specified level, if any
        records = [rec for rec in self.records if rec.levelno == self.level or self.level is None]

        if isinstance(item, Sequence):
            self._matcher_description = str(item)
            # sequence! all needs to succeed, in order
            return self._verify_sequence(item.token, records)

        # simple matcher, check if it just succeeds
        matcher = _get_matcher(item)
        self._matcher_description = str(matcher)

        if any(matcher.search(record=record) for record in records):
            result = True
        else:
            result = matcher.default_response
        return result

    def _verify_sequence(self, token, records):
        """Verify if the sequence matches ok."""
        # produce the matchers for each token item
        matchers = [_get_matcher(subitem) for subitem in token]

        # the sequence may start at any point, get sample sections and try to match
        len_matchers = len(matchers)
        for start_idx in range(len(records) - len_matchers + 1):
            section = records[start_idx:start_idx + len_matchers]

            for rec, mch in zip(section, matchers):
                if not mch.search(record=rec):
                    # matcher didn't match, this sequence is not useful
                    break
            else:
                # got to the end of the section! all matched! found it!
                return True

        # exhausted all possible sections and no complete match
        return False

    @property
    def messages(self):
        """Get all the messages in this log, to show when an assert fails."""
        if self.level is None:
            level_name = "any level"
        else:
            level_name = logging.getLevelName(self.level)
        if self.records:
            title = "for {} in {} failed; logged lines:".format(
                self._matcher_description, level_name)
        else:
            title = "for {} in {} failed; no logged lines at all!".format(
                self._matcher_description, level_name)

        messages = [title]
        for record in self.records:
            messages.append(f"     {record.levelname.upper():9s} {record.repr_content}")
        return messages

    def _get_records(self, handlers):
        """Get the record objects from the logged data in all the handlers."""
        records = []
        for handler in handlers:
            records.extend(handler.records)
        return records


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
        self.handlers = [_StdlibStoringHandler('')]
        if structlog is not None:
            sc = _StructlogCapturer()
            self.handlers.append(sc)

    def reset(self):
        """Reset all handlers."""
        for handler in self.handlers:
            handler.reset()

    def teardown(self):
        """Teardown all handlers."""
        for handler in self.handlers:
            handler.teardown()

    def __getattribute__(self, name):
        if name in ("handlers", "reset", "teardown"):
            return object.__getattribute__(self, name)

        # this is handled dinamically so we don't need to create a bunch of PyTestComparares
        # for every test, specially because most of them won't be used in that test
        _levels = object.__getattribute__(self, '_levels')
        try:
            level = _levels[name]
        except KeyError:
            raise AttributeError("'FixtureLogChecker' object has no attribute {!r}".format(name))

        return PyTestComparer(self.handlers, level)


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
