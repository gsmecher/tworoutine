#!/usr/bin/python3

"""
Double-entry style asynchronous coding.
"""

import nest_asyncio
import asyncio

__all__ = ["tworoutine"]


nest_asyncio.apply()


class tworoutine(object):

    instance = None  # starts out unbound

    def __init__(self, coroutine, instance=None):
        self.__coroutine = coroutine
        self.instance = instance

    def __get__(self, obj, type_):
        """Descriptor allowing us to behave as bound or unbound methods."""

        if obj is None:
            return self  # Unbound

        return self.__class__(self.__coroutine.__get__(obj, type_))

    def __call__(self, *args, **kwargs):
        """Stub for ordinary, serial call"""

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
