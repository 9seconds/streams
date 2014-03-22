# -*- coding: utf-8 -*-


###############################################################################


from sys import modules

from concurrent.futures import Executor, Future, ThreadPoolExecutor


###############################################################################


class SequentalExecutor(Executor):

    def __init__(self, *args, **kwargs):
        super(SequentalExecutor, self).__init__()

    def submit(self, fn, *args, **kwargs):
        future = Future()
        try:
            future.set_result(fn(*args, **kwargs))
        except Exception as exc:
            future.set_exception(exc)
        return future

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

    class GeventExecutor(Executor):

        def __init__(self, *args, **kwargs):
            super(GeventExecutor, self).__init__()
            self.worker_pool = Pool()

        def submit(self, fn, *args, **kwargs):
            greenlet = self.worker_pool.apply_async(fn, args, kwargs)
            return GreenletFuture(greenlet)

    if "gevent.monkey" in modules:
        ParallelExecutor = GeventExecutor
    else:
        ParallelExecutor = ThreadPoolExecutor
