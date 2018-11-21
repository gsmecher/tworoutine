#!/usr/bin/env python3.7

import asyncio
import tworoutine
import unittest


@tworoutine.tworoutine
async def sleepy_double_function(arg):
    await asyncio.sleep(0.01)
    return 2 * arg


class TworoutineTest(unittest.TestCase):

    # Ordinary functions
    def test_synchronous_function(self):
        assert sleepy_double_function(1) == 2

    def test_asynchronous_function(self):
        assert (
            asyncio.new_event_loop().run_until_complete((~sleepy_double_function)(2))
            == 4
        )

    # Methods
    @tworoutine.tworoutine
    async def sleepy_double_method(self, arg):
        await asyncio.sleep(0.01)
        return 2 * arg

    def test_asynchronous_method(self):
        assert (
            asyncio.new_event_loop().run_until_complete((~self.sleepy_double_method)(3))
            == 6
        )

    # Class methods
    @tworoutine.tworoutine
    @classmethod
    async def sleepy_double_classmethod(cls, arg):
        await asyncio.sleep(0.01)
        return 2 * arg

    def test_synchronous_classmethod(self):
        assert self.sleepy_double_classmethod(3) == 6

    def test_asynchronous_classmethod(self):
        assert (
            asyncio.new_event_loop().run_until_complete(
                (~self.sleepy_double_classmethod)(3)
            )
            == 6
        )

    # Static methods
    @tworoutine.tworoutine
    @staticmethod
    async def sleepy_double_staticmethod(arg):
        await asyncio.sleep(0.01)
        return 2 * arg

    def test_synchronous_staticmethod(self):
        assert self.sleepy_double_staticmethod(3) == 6

    def test_asynchronous_staticmethod(self):
        assert (
            asyncio.new_event_loop().run_until_complete(
                (~self.sleepy_double_staticmethod)(3)
            )
            == 6
        )


if __name__ == "__main__":
    try:
        unittest.main()
    except SystemExit:
        pass
