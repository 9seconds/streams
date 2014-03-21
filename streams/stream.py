# -*- coding: utf-8 -*-


###############################################################################


from __future__ import division

from itertools import chain
from multiprocessing import cpu_count

from concurrent.futures import ProcessPoolExecutor
from six import iteritems

from .executors import ParallelExecutor
from .mixins import StreamFactoryMixin, StreamFlowMixin, StreamTerminalMixin


###############################################################################


class Stream(StreamFactoryMixin, StreamFlowMixin, StreamTerminalMixin):

    def __init__(self, streamed_object=None, executor_class=ParallelExecutor):
        self.parallel_executor = None
        self.process_executor = None
        self.executor_class = executor_class
        self.length = None

        if streamed_object is None:
            streamed_object = tuple()

        if isinstance(streamed_object, Stream):
            self.parallel_executor = streamed_object.parallel_executor
            self.process_executor = streamed_object.process_executor

        if isinstance(streamed_object, dict):
            self.iterator = iteritems(streamed_object)
        else:
            self.iterator = iter(streamed_object)

        if hasattr(streamed_object, "__len__"):
            worker_count = len(streamed_object)
        else:
            worker_count = cpu_count()

        if executor_class == ProcessPoolExecutor:
            if self.process_executor is None:
                self.process_executor = ProcessPoolExecutor(worker_count)
            self.executor = self.process_executor
        else:
            if not isinstance(self.parallel_executor, executor_class):
                self.parallel_executor = executor_class(worker_count)
            self.executor = self.parallel_executor

    def __iter__(self):
        return iter(self.iterator)

    def __reversed__(self):
        return self.reversed()

    # noinspection PyTypeChecker
    def __len__(self):
        return len(self.iterator)

    @property
    def first(self):
        first_element = next(self.iterator)
        self.iterator = chain([first_element], self.iterator)
        return first_element
