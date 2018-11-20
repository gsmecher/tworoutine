#!/usr/bin/python3

'''
Double-entry style asynchronous coding.
'''

import nest_asyncio
import asyncio

__all__ = ["tworoutine"]


class tworoutine(object):

    instance = None  # starts out unbound

    def __init__(self, coroutine, instance=None):
        self.__coroutine = coroutine
        self.instance = instance
        nest_asyncio.apply()

    def __get__(self, instance, owner):
        '''Descriptor allowing us to behave as bound or unbound methods.'''

        if instance is None:
            return self  # Unbound, with nothing to bind to.

        if self.instance:
            return self.instance.__get__(instance, owner)  # Bound.

        # Otherwise, we're an unbound instance with a binding provided.
        # Generate a captive, bound, subclass and return it.
        bound = self.__class__(self.__coroutine, instance)
        return bound

    def __call__(self, *args, **kwargs):
        '''Stub for ordinary, serial call'''

        # By default, presume a fancy asynchronous version has been coded and
        # invoke it synchronously. This is often all the serial version needs
        # to do anyways.
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
        coroutine = (~self)(*args, **kwargs)
        return loop.run_until_complete(coroutine)

    def __invert__(self):
        return self.__coroutine

# vim: sts=4 ts=4 sw=4 tw=78 smarttab expandtab
