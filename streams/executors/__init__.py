# -*- coding: utf-8 -*-


###############################################################################


from sys import modules

from .executors import SequentalExecutor, ThreadPoolExecutor, \
    ProcessPoolExecutor

if "gevent.monkey" in modules:
    from .gevent import GeventExecutor
    ParallelExecutor = GeventExecutor
else:
    ParallelExecutor = ThreadPoolExecutor
