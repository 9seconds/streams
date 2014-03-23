# -*- coding: utf-8 -*-


###############################################################################


from collections import deque
from itertools import islice
from sys import exc_info

from six import reraise
# noinspection PyUnresolvedReferences
from six.moves import zip as izip


###############################################################################


class PoolOfPoolsMixin(object):

    @staticmethod
    def dummy_callback(*args, **kwargs):
        pass

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

    # noinspection PyUnresolvedReferences
    def expand(self, expand_to):
        self._max_workers += expand_to

    # noinspection PyUnresolvedReferences
    def map(self, fn, *iterables, **kwargs):
        callback = kwargs.get("callback", self.dummy_callback)
        worker_count = kwargs.get("required_workers", self._max_workers)
        payload = deque()
        args_iterator = izip(*iterables)

        for args in islice(args_iterator, worker_count):
            payload.append(self.submit(fn, *args))
        for args in args_iterator:
            yield self.get_first(payload)
            payload.append(self.submit(fn, *args))
        while payload:
            yield self.get_first(payload)

        callback(self, worker_count)
