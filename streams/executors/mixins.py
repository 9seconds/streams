# -*- coding: utf-8 -*-
"""
This module provides :py:class:`PoolOfPoolMixin` only. Basically you need to
mix it into :py:class:`concurrent.futures.Executor` implementation and it will
be possible to use it with :py:class:`PoolOfPools`.
"""


###############################################################################


from collections import deque
from itertools import islice
from sys import exc_info

from six import reraise
# noinspection PyUnresolvedReferences
from six.moves import zip as izip


###############################################################################


class PoolOfPoolsMixin(object):
    """
    Mixin to support :py:class:`PoolOfPools` execution properly.

    Basically it replaces map implementation and provides some additional
    interface which helps :py:class:`PoolOfPools` to manage executor instance.
    Current implementation supports expanding only (dynamically increases)
    the number of workers.
    """

    @staticmethod
    def dummy_callback(*args, **kwargs):
        """
        Just a dummy callback if no :py:class:`PoolOfPools.worker_finished`
        is supplied for the mapper. Basically does nothing. Literally nothing.
        Good thing though, no bugs.
        """
        pass

    # noinspection PyBroadException
    @staticmethod
    def get_first(queue):
        """
        Extracts the result of the execution from the first element of the
        queue (to support order since a ``map`` is ordering function). Also
        it tries to handle exceptions if presented in the same way as
        :py:class:`concurrent.futures.ThreadPoolExecutor` or
        :py:class:`concurrent.futures.ProcessPoolExecutor` do.

        .. note::
            It relies on given implementation of ``map`` method in both
            :py:class:`concurrent.futures.ThreadPoolExecutor` and
            :py:class:`concurrent.futures.ProcessPoolExecutor` so if you
            see some differences in behaviour please create an issue.
        """
        first_future = queue.popleft()
        try:
            result = first_future.result()
        except:
            for future in queue:
                future.cancel()
            reraise(*exc_info())
        else:
            return result
        finally:
            first_future.cancel()

    # noinspection PyUnresolvedReferences
    def expand(self, expand_to):
        """
        The hack to increase an amount of workers in executor.

        :param int expand_to: The amount of worker we need to add to the
                              executor.

        .. note::
            It works perfect with :py:class:`GeventExecutor` and
            :py:class:`concurrent.futures.ThreadPoolExecutor` but has some
            issues with :py:class:`concurrent.futures.ProcessPoolExecutor`.

            It increases the amount of workers who manage task queue but
            it is not possible to expand queue itself in a good way (current
            implementation has a limit of tasks in the queue).
        """
        assert expand_to >= 0
        self._max_workers += expand_to

    # noinspection PyUnresolvedReferences
    def map(self, fn, *iterables, **kwargs):
        """
        New implementation of concurrent mapper.

        It has 2 new arguments: ``callback`` and ``required_workers``

        :param Callable callback:    Callback to execute after map is done
        :param int required_workers: The amount of workers we have to use
                                     for this map procedure.

        It differs from default implementation in 2 ways:
            1. It uses the limit of workers (``required_workers``). It can be
               less than max workers defined on executor initialization
               hence it is possible to utilize the same executor for several
               tasks more efficient.
            2. It doesn't create a list of futures in memory. Actually it
               creates only ``required_workers`` amount of futures and tries
               to keep this count the same during whole procedure. Yes, it is
               not naturally concurrent execution because it just submits
               task by task but on big iterables it utilizes as less memory
               as possible providing reasonable concurrency.
        """
        callback = kwargs.get("callback", self.dummy_callback)
        worker_count = kwargs.get("required_workers", self._max_workers)
        worker_count = max(worker_count, 1)
        queue = deque()
        args_iterator = izip(*iterables)

        for args in islice(args_iterator, worker_count):
            queue.append(self.submit(fn, *args))
        for args in args_iterator:
            yield self.get_first(queue)
            queue.append(self.submit(fn, *args))
        while queue:
            yield self.get_first(queue)

        callback(self, worker_count)
