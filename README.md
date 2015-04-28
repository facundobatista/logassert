Log Assertion
=============


What?
-----

A simple Log Assertion mechanism for Python unittests.


Why?
----

As is vox populi, you must also test the logging calls in your programs.

With ``logassert`` this now is very easy.


Awesome! How to use it?
-----------------------

All you need to do is to call this module's ``setup()`` passing the test case
instance, and the logger you want to supervise.

Like::

    class MyTestCase(unittest.TestCase):
        """Example."""

        def setUp(self):
            logassert.setup(self, 'mylogger')

In the example, ``mylogger`` is the name of the logging to supervise. If 
different subsystems of your code log in other loggers, this tester 
won't notice.

Then, to use it, just call the ``assertLogged`` method and it's family, 
passing all the strings you want to find. 

Example::

        def test_blah(self):
            (...)
            self.assertLoggedDebug('secret', 'life', '42')

That line will check that "secret", "life" and "42" are all logged in the 
same logging call, in DEBUG level.

So, if you logged this, the test will pass::

    logger.debug("The secret of life, the universe and everything is %d", 42)

Note that the message checked is the one with all parameters replaced.

But if you logged any of the following, the test will fail (the first because 
it misses one of the string, the second because it has the wrong log level)::

    logger.debug("The secret of life, the universe and everything is lost")
    logger.info("The secret of life, the universe and everything is 42")


Nice! But...
------------

If you need help, or have any question, or found any issue, please open a 

https://github.com/facundobatista/logassert/issues

Thanks in advance for your time.
