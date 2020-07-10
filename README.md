# Log Assertion

![Python package](https://github.com/facundobatista/logassert/workflows/Python%20package/badge.svg)

## What?

A simple log assertion mechanism for Python unittests.


## Why?

As is vox populi, you must also test the logging calls in your programs.

With `logassert` this is now very easy.


## What can I test?

You'll have at disposition several assertion methods:

- `self.assertLogged` / `assert_logged`: will check that the strings 
  were logged, no matter at which level

- `self.assertLoggedLEVEL` / `assert_LEVEL` (being LEVEL one of error, 
  warning, info, or debug): will check that the strings were logged at 
  that specific level.

- `self.assertNotLogged` / `assert_not_logged`: will check that the 
  strings were NOT logged, no matter at which level

- `self.assertNotLoggedLEVEL` / `assert_not_LEVEL` (being LEVEL one of 
  error, warning, info, or debug): will check that the strings were NOT 
  logged at that specific level.


## Awesome! How to use it?


### For pytest

All you need to do is to declare `logged` in your test arguments, it works
just like any other fixture.

Example:

```python
def test_bleh(logged)
    (...)
    logged.assert_debug('secret', 'life', '42')
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


## Nice! But...

If you need help, or have any question, or found any issue, please open a
ticket [here](https://github.com/facundobatista/logassert/issues/new).

Thanks in advance for your time.