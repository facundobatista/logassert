# Log Assertion

![Tests](https://github.com/facundobatista/logassert/actions/workflows/tests.yml/badge.svg)

## What?

A simple log assertion mechanism for Python unittests.


## Why?

As is vox populi, you must also test the logging calls in your programs.

With `logassert` this is now very easy.


### Why is it easy?

Because it provides a simple and expressive way to use it in the unit tests (see next section) but also because when the assertion fails, it presents a useful report that helps you to find out why it is failing.

For example, this may be a case when the logged line is slightly different:

Actual code:

```
    value = "123"
    logger.debug("Received value is %r", value)
```

The unit test assertion:
```
    assert "Received value is 123" in logs.debug
```

The report you get as it failed:
```
    AssertionError: assert for Regex("Received value is 123") in DEBUG failed; logged lines:
           DEBUG     "Received value is '123'"
    )
```

Or a case where the logged line is ok, but the level is incorrect:

Actual code:

```
    value = "123"
    logger.debug("Received value is %s", value)
```

The unit test assertion:
```
    assert "Received value is \d+" in logs.info
```

The report you get as it failed:
```
    AssertionError: assert for Regex("Received value is \d+") in DEBUG failed; logged lines:
           INFO      "Received value is 123"
    )
```


# Awesome! How do I use logassert?

After [installing](#how-to-install), the same functionality is exposed in two very different ways, one that fits better the *pytest semantics*, the other one more suitable for *classic unit tests*.

## For pytest

All you need to do is to declare `logs` in your test arguments, it works
just like any other fixture.

Then you just check (using `assert`, as usual with *pytest*) if a specific
line is in the logs for a specific level.

Example:

```python
def test_bleh(logs)
    (...)
    assert "The meaning of life is 42!" in logs.debug
```

Actually, the line you write is a regular expression, so you can totally
do (in case you're not exactly sure which the meaning of life is):

```python
    assert "The meaning of life is \d+!" in logs.debug
```

The indicated string is searched to be inside the log lines, it doesn't
need to be exact whole line. If you want that, just indicate it as with
any regular expression:

```python
    assert "^The meaning of life is \d+!$" in logs.debug
```

In a similar way you can also express the desire to check if it's at the
beginning or at the end of the log lines.

> **NOTE**: the message checked is the formatted one, after the logging system replaced all the parameters in the template and built the final string. In other words, if the code is `logger.debug("My %s", "life")`, the verification will be done in the final `My life` string.

If you want to verify that a text was logged, no matter at which level,
just do:

```python
    assert "The meaning of life is 42" in logs.any_level
```

To verify that some text was NOT logged, just juse the Python's syntax!
For example:

```python
    assert "A problem happened" not in logs.error
```

### But I don't like regexes, I want the exact string

Then you just import `Exact` from `logassert` and wrap the string
with that.

For example, in this case the `..` means exactly two dots, no regex
semantics at all:

```python
    assert Exact("The meaning of life is ..") in logs.any_level
```


### Anyway, I liked old behaviour of searching multiple strings

Then you may want to import `Multiple` from `logassert` and wrap the
different strings you had in each call for the classic behaviour.

For example:

```python
    assert Multiple("life", "meaning", "42") in logs.any_level
```


### What if I want to check that nothing was logged?

The simplest way to do it is to use the `NOTHING` verifier that you can
import from `logassert`:

```python
    assert NOTHING in logs.debug
```

Note that it doesn't make sense to use it by the negative (`...NOTHING not in logs...`):
is no really useful at testing level to know that "something was logged", you should
improve the test to specifically verify *what* was logged.


### Breaking the "per line barrier"

Sometimes it's useful to verify that several lines were logged, and that
those lines are logged one after the other, as they build a "composite
message".

To achieve that control on the logged lines you can use the `Sequence`
helper, that receives all the lines to verify (regexes by default, but
you can use the other helpers there):

```python
    assert Sequence(
        "Got 2 errors and \d+ warnings:",
        Exact("  error 1: foo"),
        Exact("  error 2: bar"),
    ) in logs.debug
```


### Examples

After logging...

```python
    person = "madam"
    item = "wallet"
    logger.debug("Excuse me %s, you dropped your %s", person, item)
```

...the following test will just pass:

```python
    assert "Excuse me .*?, you dropped your wallet" in logs.debug
```

However, the following will fail (different text!)...

```python
    assert "Excuse me .*?, you lost your wallet" in logs.debug
```

...producing this message in your tests:

```
assert for regex 'Excuse me .*?, you lost your wallet' check in DEBUG, failed; logged lines:
      DEBUG     'Excuse me madam, you dropped your wallet'
```

This one will also fail (different level!)...

```python
    assert "Excuse me .*?, you dropped your wallet" in logs.info
```

...producing this message in your tests:

```
assert for regex 'Excuse me .*?, you dropped your wallet' check in INFO, failed; logged lines:
       DEBUG     'Excuse me madam, you dropped your wallet'
```

A more complex example, with several log lines, and a specific assertion:

```python
    logger.info("Starting system")
    places = ['/tmp/', '~/temp']
    logger.debug("Checking for config XYZ in all these places %s", places)
    logger.warning("bad config XYZ")

    assert "bad config XYZ" in logs.debug
```

See how the test failure message is super helpful:

```
assert for regex 'bad config XYZ' check in DEBUG, failed; logged lines:
       INFO      'Starting system'
       DEBUG     "Checking for config XYZ in all these places ['/tmp/', '~/temp']"
       WARNING   'bad config XYZ'

```

### What about repeated verifications?

Sometimes it's needed to verify that something if logged only once (e.g.
welcoming messages). In this cases it's super useful to use the `reset`
method.

See the following test sequence:

```python
def test_welcoming message(logs):
    custom_logger.info("foo")  # first log! it should trigger the welcoming message
    assert "Welcome" in logs.info

    logs.reset()
    custom_logger.info("foo")  # second log! it should NOT trigger the welcoming message
    assert "Welcome" not in logs.info
```


## For classic TestCases

All you need to do is to call this module's `setup()` passing the test case
instance, and the logger you want to supervise.

Like

```python
class MyTestCase(unittest.TestCase):
    """Example."""

    def setUp(self):
        logassert.setup(self, 'mylogger')
```

In the example, `mylogger` is the name of the logging to supervise. If
different subsystems of your code log in other loggers, this tester
won't notice.

Then, to use it, just call the `assertLogged` method and it's family,
passing all the strings you want to find. This is the default behaviour for
backwards compatibility.

Example:

```python
    def test_blah(self):
        (...)
        self.assertLoggedDebug('secret', 'life', '42')
```

That line will check that "secret", "life" and "42" are all logged in the
same logging call, in DEBUG level.

So, if you logged this, the test will pass:

```python
logger.debug("The secret of life, the universe and everything is %d", 42)
```

Note that the message checked is the one with all parameters replaced.

But if you logged any of the following, the test will fail (the first because
it misses one of the string, the second because it has the wrong log level)::

```python
logger.debug("The secret of life, the universe and everything is lost")
logger.info("The secret of life, the universe and everything is 42")
```

### What can I test?

You'll have at disposition several assertion methods:

- `self.assertLogged`: will check that the strings
  were logged, no matter at which level

- `self.assertLoggedLEVEL` (being LEVEL one of Error,
  Warning, Info, or Debug): will check that the strings were logged at
  that specific level.

- `self.assertNotLogged`: will check that the
  strings were NOT logged, no matter at which level

- `self.assertNotLoggedLEVEL` (being LEVEL one of
  Error, Warning, Info, or Debug): will check that the strings were NOT
  logged at that specific level.


## Support for structured logs

The [structlog](https://pypi.org/project/structlog/) library is very commonly used by developers. It provides a simple way of logging using messages and dictionaries with structured data that later are processed in powerful ways.

For example you can do:

```
    ...
    result = "success"
    code = 37
    logger.debug("Process finished correctly", result=result, code=code)
```

How do you test that? Don't panic! `logassert` supports `structlog` :)

It is very similar to the regular logging checks, but formalizing that there is a structure with a message and other fields:

```
    assert Struct("Process finished", result="success") in logs.debug
```

When a string is used in the main message or any of the field values, the regular `logassert` rules apply (by default it is a regular expression and is searched *in* the logged text) but you can use all the power of the helpers, like checking for the exact string...

```
    assert Struct(Exact("Process finished correctly"), result="success") in logs.debug
```

...or using multiple strings...

```
    assert Struct(Multiple("correctly", "finished"), result="success") in logs.debug
```

... etc.

If the field value is not a string, it's matches just for equality:

```
    assert Struct("finished", code=37) in logs.debug
    assert Struct("finished", code=3) not in logs.debug
```


### Complete structures

The previous examples just verified that the indicated fields exist in the logged lines, but they do NOT assert that those are ALL the logged fields.

If you want to check that the given message and fields match but also verify that the those are all the logged fields, you need to use `CompleteStruct`. E.g.:

```
    assert CompleteStruct("finished", code=37, result="success") in logs.debug
```

### For structlog you need... structured logs

You may have `structlog` installed and be using it properly like `logger.info("some text", foo="bar")`, but if `structlog` is configured to use `structlog.stdlib.BoundLogger` the logged message and keywords will be mashed up in a big string, so you lose the ability of "struct testing" with `logassert`.

It is fine, though, because `logassert` registers it's own logger class when the `logs` fixture kicks in. However, if in your project `structlog` is also configured to cache the logger on first use, the original logger with stdlib behaviour will *always* be used.

For example, you may have the following in your project's setting / configuration:

```
structlog.configure(
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
```

While using that `wrapper_class` is kind of OK, the real problem comes with the second line. You may solve it in the settings / configuration, or add an automatic fixture in `conftest.py` to change `cache_logger_on_first_use` back to `False`.


# How to install logassert

`logassert` is a very small pure Python library, easiest way to install is from PyPI:

```
    pip install logassert
```


# How to help with development

If you actually want to work in `logassert` itself, clone this repository or a fork that you may create in Github, and then:


```
    python3 -m venv env
    source env/bin/activate
    pip install .[dev]
    ./test
```

That will create a virtualenv, install dependencies needed for development, and run tests. From there you're set to continue.


# Nice! But...

If you need help, or have any question, or found any issue, please open a
ticket [here](https://github.com/facundobatista/logassert/issues/new).

Thanks in advance for your time.
