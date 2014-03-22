# -*- coding: utf-8 -*-


###############################################################################


from collections import deque
from itertools import islice
from sys import modules, exc_info

from concurrent.futures import Executor, Future, \
    ThreadPoolExecutor as BaseThreadPoolExecutor, \
    ProcessPoolExecutor as BaseProcessPoolExecutor

from six import reraise
# noinspection PyUnresolvedReferences
from six.moves import zip as izip


###############################################################################


class ProperIterableMapMixin(object):

    # noinspection PyBroadException
    @staticmethod
    def get_first(payload):
        first_future = payload.popleft()
        try:
            result = first_future.result()
        except:
            for future in payload:
                future.cancel()
            reraise(*exc_info())
        else:
            return result
        finally:
            first_future.cancel()

    # noinspection PyUnresolvedReferences,PyUnusedLocal
    def map(self, fn, *iterables, **kwargs):
        payload = deque(maxlen=self._max_workers)
        args_iterator = izip(*iterables)

        for args in islice(args_iterator, self._max_workers):
            payload.append(self.submit(fn, *args))
        for args in args_iterator:
            yield self.get_first(payload)
            payload.append(self.submit(fn, *args))
        while payload:
            yield self.get_first(payload)


class SequentalExecutor(ProperIterableMapMixin, Executor):

    # noinspection PyUnusedLocal
    def __init__(self, *args, **kwargs):
        super(SequentalExecutor, self).__init__()
        self._max_workers = 1

    def submit(self, fn, *args, **kwargs):
        future = Future()
        try:
            future.set_result(fn(*args, **kwargs))
        except Exception as exc:
            future.set_exception(exc)
        return future


class ThreadPoolExecutor(ProperIterableMapMixin, BaseThreadPoolExecutor):
    pass


class ProcessPoolExecutor(ProperIterableMapMixin, BaseProcessPoolExecutor):
    pass


try:
    from gevent import Timeout
    from gevent.pool import Pool
except ImportError:
    ParallelExecutor = ThreadPoolExecutor
else:
    class GreenletFuture(Future):

        def __init__(self, greenlet):
            super(GreenletFuture, self).__init__()
            self.greenlet = greenlet

        def execute(self, timeout=None):
            try:
                processed_result = self.greenlet.get(True, timeout)
            except Timeout as exc:
                self.set_exception(exc)
            else:
                if self.greenlet.exception:
                    self.set_exception(self.greenlet.exception)
                else:
                    self.set_result(processed_result)

        def result(self, timeout=None):
            self.execute(timeout)
            return super(GreenletFuture, self).result(timeout)

        def exception(self, timeout=None):
            self.execute(timeout)
            return super(GreenletFuture, self).exception(timeout)

        def cancel(self):
            self.greenlet.kill()
            return super(GreenletFuture, self).cancel()

    class GeventExecutor(ProperIterableMapMixin, Executor):

        # noinspection PyUnusedLocal
        def __init__(self, *args, **kwargs):
            super(GeventExecutor, self).__init__()
            self._max_workers = 100
            self.worker_pool = Pool(self._max_workers)

        def submit(self, fn, *args, **kwargs):
            greenlet = self.worker_pool.apply_async(fn, args, kwargs)
            return GreenletFuture(greenlet)

    if "gevent.monkey" in modules:
        ParallelExecutor = GeventExecutor
    else:
        ParallelExecutor = ThreadPoolExecutor
