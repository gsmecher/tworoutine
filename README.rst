Tworoutines
===========

This library allows a style of coding in Python that permits easy mixing of
synchronous and asynchronous code. As part of the control software for large
microwave telescopes (including the `South Pole Telescope`_), we have been
using this style of code under a Tornado / Python 2.x stack with success.

Unfortunately, architectural changes in Python 3.7 conspire against the
`@tworoutine`.  In the hopes of contributing to a lively discussion about
Python's asynchronous ecosystem, I have mocked up a Python 3.7 implementation
and released it here.

Introduction
------------

Asynchronous coding in Python was pioneered by third-party libraries like
`Twisted`_, `Tornado`_, and `gevent`_. An "official" event-loop implementation
landed in `Python 3.4
<https://docs.python.org/3.4/library/asyncio-task.html>`_, and was expanded
significantly in `Python 3.7
<https://docs.python.org/3/library/asyncio.html>`_. A new breed of asynchronous
libraries like `curio`_ and `trio`_ continue to push the boundaries beyond
what's "normal" in the space.

There are also some excellent (and opinionated) articles about Python's
asynchronous ecosystem. I don't always agree with them and I don't intend to
recapitulate them.  To allow me to get the point, though, I will provide a few
links that set the stage for what follows.

* `PEP 3156 -- Asynchronous IO Support Rebooted: the "asyncio" Module <https://www.python.org/dev/peps/pep-3156/>`_
* `I don't understand Python's Asyncio <http://lucumr.pocoo.org/2016/10/30/i-dont-understand-asyncio/>`_
* `How the heck does async/await work in Python 3.5? <https://snarky.ca/how-the-heck-does-async-await-work-in-python-3-5/>`_
* `Controlling Python Async Creep <https://hackernoon.com/controlling-python-async-creep-ec0a0f4b79ba>`_

Of these, the last one is probably the most interesting because it identifies
and attempts to address the same problem we run into when designing telescope
tuning software: asynchronous and synchronous coding styles occupy different
universes in Python, but it is exteremly useful to mix them freely.

To motivate mixing synchronous and asynchronous code, here is a short
description of the kind of code we write for tuning telescopes.

Coding for Telescopes
---------------------

My day job includes work on CMB telescopes including the `South Pole
Telescope`_ in `Antarctica <https://goo.gl/maps/SNnrUyLcFkq>`_ and the `Simons
Array`_ on Chile's Atacama Plateau.

The `readout electronics <https://arxiv.org/abs/1407.3161>`_ in these
telescopes is a large array of `software defined radios
<https://arxiv.org/pdf/1008.4587.pdf>`_, with many thousands of transmitters
and receivers used to bias and measure the leftover signature of the Big Bang.
These radios are implemented in hundreds of custom boards hosting `FPGAs
<https://www.xilinx.com/products/silicon-devices/fpga/kintex-7.html>`_
installed in crates near the telescope, and controlled by a PC.  This PC gets
the system up and running, controls cryogenic refrigerators, aims the
telescope, and captures the torrent of data it produces.

The entire tuning, control, and analysis stack makes very heavy use of Python,
along with C, C++, and VHDL. (I am inexpressibly grateful to the many
open-source communities we rely on, and it is a great privilege when I can give
back in some capacity.)

As you can imagine, we don't just deploy code straight onto the telescope.
Along with the telescopes themselves are small-scale installations ranging from
a circuit board or two on a benchtop, to crates of cryogenic equipments at
university labs around the world. During development, code might be running
in a `Jupyter notebook <http://jupyter.org/>`_ or an `IPython shell
<https://ipython.org/>`_, perhaps with a small crate of electronics or nothing
at all. Here, interactive REPL sessions are used to prototype algorithms,
explore data, and try out new tuning and analysis techniques.

For an algorithm to be useful in deployment, however, it needs to run at scale.
Here's where we use asynchronous code heavily: command interactions with many
hundreds of circuit boards are a natural fit for asynchronous coding styles.
This leads to the following workflow:

* Prototype code, probably synchronous and focused on proofing out an algorithm
  or technique;
* Test for function on a small-scale deployment, likely in an interactive
  (ipython) environment;
* *Re-code* the algorithm using an asynchronous style; and
* Integration testing, optimization, and deployment.

This approach has advantages:

1. When developing a proof-of-concept, developers are able to ignore
   performance and focus on the problem (physics, instrumentation, cryogenics,
   electronics) that they are attempting to address.
2. During prototyping, when interactive exploration is most useful, synchronous
   code promotes use of environments such as IPython or Jupyter.

However, this workflow has three major disadvantages:

1. It's clumsy: it requires writing and testing a synchronous version, then
   shifting it wholesale to an asynchronous environment.  It is easy to imagine
   this workflow looping back on itself as bugs are discovered or introduced
   along the way.
2. The synchronous version *never stops being useful*, despite not scaling to
   telescope-level performance. We would often much rather have the simpler
   semantics, more predictable control flow, and shorter error traces associated
   with a synchronous call when debugging or experimenting.  In addition, it can
   be conveniently invoked in a REPL environment -- invaluable if the telescope is
   operating and we need to do some quick hand-tuning.
3. It's not composable. Over the years, we have build up libraries of useful
   tuning and control algorithms, and as long as synchronous and asynchronous
   code is kept distinct, we cannot meaningfully compose algorithms out of
   smaller pieces without two implementations of everything.

Asking developers to maintaining two versions under different coding idioms
(and expecting to keep the versions synchronized) is resolving a technical flaw
by requiring skilled labourers to do menial work; this is often an expensive
mistake.  (Interactive use of asynchronous code is getting easier in IPython
7.0 due to the `autoawait
<https://ipython.readthedocs.io/en/stable/interactive/autoawait.html>`_
functionality. This extension addresses the second but not the third point.)

Instead, we are looking for a way to freely mix asynchronous and synchronous
coding styles.

Enter the `@tworoutine`
-----------------------

What's a `@tworoutine`? It is a *synchronous* wrapper around an *asynchronous*
function, allowing a single piece of code to be called in either idiom.

(If you are following along at home, you will need the `source code
<https://github.com/gsmecher/tworoutine>`_. You will also need `nest_asyncio
<https://github.com/erdewit/nest_asyncio>`_.)

.. code:: python

    import tworoutine
    import asyncio

    @tworoutine.tworoutine
    async def double_slowly(x):
        await asyncio.sleep(0.1)
        return 2*x

How can we call this function synchronously? Just call it!

.. code:: python

    >>> double_slowly(1)
    2

How did this work? The `@tworoutine` decorator returns a class whose `__call__`
method is a synchronous wrapper that obtains an event loop and invokes the
asynchronous code, blocking until it's complete. Because we want synchronous
calling to be convenient and carpal-tunnel-friendly, that's the default.

If there's already an event loop running, this code is reasonably efficient
(aside from being a blocking call, of course!) Any asynchronous events already
queued in the event loop are allowed to proceed alongside this one. Only the
current execution context is blocked until the coroutine completes.

So much for synchronous calls. How can we call this function asynchronously? We
first have to undo or "invert" the wrapper and obtain a reference back to the
coroutine.

.. code:: python

    >>> (~double_slowly)(2)
    <coroutine object double_slowly at 0x7f5d494fd348>

With the exception of the invert operator around the function name, this is
ordinary asynchronous code; there is no additional overhead except for the
operator itself.  Here is a complete example showing mixed coding styles within
an event loop:

.. code:: python

    async def main():
        # Run asynchronously
        r = await (~double_slowly)(2)
        print(r)

        # Run synchronously within an event loop
        r2 = double_slowly(3)
        print(r2)

    # try asynchronous entry
    asyncio.run(main())

The obvious benefit, here, is the ability to call asynchronous code
synchronously when we're too lazy to carry around an event loop or deal with
the `turtles-all-the-way-down
<https://medium.com/@davealexis/this-is-why-i-consider-the-async-await-pattern-to-be-like-a-virus-e029d95fcba1>`_
nature of Python's asynchronous coding idiom.

Of Course There's A Catch
-------------------------

`@tworoutine`'s days are probably numbered. This style of coding has been
implicitly but firmly rejected by Python developers:

* `Issue 22239: asyncio: nested event loop <https://bugs.python.org/issue22239>`_

We have been using this approach (implemented on Python 2.7 and Tornado <4.5)
for several years now at the South Pole and elsewhere, and we will have to
adapt.

To complete a synchronous `@tworoutine` call, we need to obtain an event loop,
schedule the asynchronous (decorated) call, and block until it is complete.
Currently there is no way to do that in Python 3.7 asyncio without patching it.
Asynchronous code at any point in the call stack must be linked to the event
loop via asynchronous calls only, all the way up.

To work around this problem in the Python 3.7 code shown here, I have used the
`nest_asyncio <https://github.com/erdewit/nest_asyncio>`_ monkey patch. It is a
short and effective piece of code, but it runs against Python orthodoxy and
adopting this kind of patch in production risks being stranded by changes to
Python's core libraries.

Without this patch, we are able to upgrade as far as Tornado 4.5 on Python 3.x,
but `Tornado 5.0 <https://github.com/jupyter/notebook/issues/3397>`_ moves to
an asyncio event loop and we are suddenly unable to upgrade.

Disclaimer
----------

The code examples here have been forward-ported from Python 2.7 and Tornado 4.5
to Python 3.7 and "pure" asyncio. It's an experiment -- this is not
production code!

.. _asyncio: https://docs.python.org/3/library/asyncio.html
.. _twisted: https://twistedmatrix.com
.. _tornado: https://tornadoweb.org
.. _gevent: https://gevent.org
.. _curio: http://github.com/dabaez/curio
.. _trio: http://trio.readthedocs.io
.. _South Pole Telescope: https://pole.uchicago.edu/spt/
.. _Simons Array: https://arxiv.org/abs/1512.07299
