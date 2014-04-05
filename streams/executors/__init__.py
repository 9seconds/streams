# -*- coding: utf-8 -*-
"""
This module provides different implementation of concurrent executors suitable
to work with :py:class:`streams.poolofpools.PoolOfPools`. If Gevent is
available then you can also import
:py:class:`streams.executors._gevent.GeventExecutor` here.

Also it has some class called :py:class:`streams.executors.ParallelExecutor`.
This is dynamically calculated class for default concurrent execution. If
code is monkey patched by Gevent, then it uses
:py:class:`streams.executors._gevent.GeventExecutor`. Otherwise -
:py:class:`streams.executors.executors.ThreadPoolExecutor`.
"""


###############################################################################


from sys import modules

from .executors import SequentalExecutor, ThreadPoolExecutor, \
    ProcessPoolExecutor


ParallelExecutor = ThreadPoolExecutor
try:
    import gevent
except ImportError:
    pass
else:
    from ._gevent import GeventExecutor
    if "gevent.monkey" in modules:
        ParallelExecutor = GeventExecutor
