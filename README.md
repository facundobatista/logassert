# Log Assertion

![Python package](https://github.com/facundobatista/logassert/workflows/Python%20package/badge.svg)

## What?

A simple log assertion mechanism for Python unittests.


## Why?

As is vox populi, you must also test the logging calls in your programs.

With `logassert` this is now very easy.


# Awesome! How do I use it?

The same functionality is exposed in two very different ways, one that fits better the *pytest semantics*, the other one more suitable for classic unit tests.

## For pytest

All you need to do is to declare `logs` in your test arguments, it works
just like any other fixture.

Then you just check (using `assert`, as usual with *pytest*) if a specific 
line is in the logs for a specific level.

Example:

```python
def test_bleh(logs)
    (...)
    assert "The meaning of life is 42" in logs.debug
```

Actually, the line you write is a regular expression, so you can totally 
do (in case you're not exactly sure which the meaning of life is):

```python
    assert "The meaning of life is \d+" in logs.debug
```

The indicated string is searched to be inside the log lines, it doesn't 
need to be exact whole line. If you want that, just indicate it as with
any regular expression:

```python
    assert "^The meaning of life is \d+$" in logs.debug
```

In a similar way you can also express the desire to check if it's at the 
beginning or at the end of the log lines.

> **NOTE**: the message checked is the final one, after the logging system 
replaced all the indicated parameters in the indicated string.

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
    logger.info("foo")  # first log! it should trigger the welcoming message
    assert "Welcome" in logs.info

    logs.reset()
    logger.info("foo")  # second log! it should NOT trigger the welcoming message
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



# Nice! But...

If you need help, or have any question, or found any issue, please open a
ticket [here](https://github.com/facundobatista/logassert/issues/new).

Thanks in advance for your time.
