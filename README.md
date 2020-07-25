# Log Assertion

![Python package](https://github.com/facundobatista/logassert/workflows/Python%20package/badge.svg)

## What?

A simple log assertion mechanism for Python unittests.


## Why?

As is vox populi, you must also test the logging calls in your programs.

With `logassert` this is now very easy.


## Awesome! How do I use it?

The same functionality is exposed in two very different ways, one that fits better the *pytest semantics*, the other one more suitable for classic unit tests.

### For pytest

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

Note that the message checked is the final one, after the logging system 
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

# FIXME

This one will also fail (different level!)...

```python
assert "Excuse me .*?, you dropped your wallet" in logs.info
```

...producing this message in your tests:

# FIXME





### For classic TestCases

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
passing all the strings you want to find.

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



## Nice! But...

If you need help, or have any question, or found any issue, please open a
ticket [here](https://github.com/facundobatista/logassert/issues/new).

Thanks in advance for your time.
