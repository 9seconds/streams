# -*- coding: utf-8 -*-


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
    from .gevent import GeventExecutor
    if "gevent.monkey" in modules:
        ParallelExecutor = GeventExecutor
