# -*- coding: utf-8 -*-


###############################################################################


from heapq import heapify, heapreplace, _heapify_max, _heappushpop_max
from itertools import chain, islice
from operator import add, truediv
from re import compile as regex_compile

from concurrent.futures import ProcessPoolExecutor

# noinspection PyUnresolvedReferences
from six.moves import map as imap, reduce as reduce_func, filter as ifilter

from .executors import ParallelExecutor, SequentalExecutor
from .iterators import seed, distinct, peek, accumulate
from .utils import filter_map, not_predicate, key_mapper, value_mapper, \
    make_list, filter_keys, filter_values


###############################################################################


class StreamFactoryMixin(object):

    @classmethod
    def concat(cls, *streams):
        return cls(chain(*streams))

    @classmethod
    def iterate(cls, function, seed_value):
        return cls(seed(function, seed_value))


# noinspection PyUnresolvedReferences
class StreamFlowMixin(object):

    def filter(self, predicate, parallel=True):
        if parallel:
            # noinspection PyTypeChecker
            filtered = self.map(filter_map(predicate), self.iterator)
            filtered = (item for result, item in filtered if result)
        else:
            filtered = ifilter(predicate, self.iterator)
        return self.__class__(filtered, self.executor_class)

    def regexp(self, regexp, flags=0):
        regexp = regex_compile(regexp, flags)
        filtered = ifilter(lambda item: regexp.match(item), self.iterator)
        return self.__class__(filtered, self.executor_class)

    def divisible_by(self, number):
        filtered = ifilter(lambda item: item % number, self.iterator)
        return self.__class__(filtered, self.executor_class)

    def evens(self):
        return self.divisible_by(2)

    def odds(self):
        filtered = ifilter(lambda item: item % 2 != 0, self.iterator)
        return self.__class__(filtered, self.executor_class)

    def exclude(self, predicate, parallel=True):
        return self.filter(not_predicate(predicate), parallel)

    def exclude_nones(self):
        filtered = ifilter(lambda item: item is not None, self.iterator)
        return self.__class__(filtered, self.executor_class)

    def only_trues(self):
        filtered = ifilter(lambda item: bool(item), self.iterator)
        return self.__class__(filtered, self.executor_class)

    def map(self, predicate, parallel=True):
        mapper = self.executor.map if parallel else imap
        return self.__class__(mapper(predicate, self.iterator),
                              self.executor_class)

    def value_mapper(self, predicate, parallel=True):
        return self.map(value_mapper(predicate), parallel)

    def key_mapper(self, predicate, parallel=True):
        return self.map(key_mapper(predicate), parallel)

    def distinct(self):
        return self.__class__(distinct(self.iterator), self.executor_class)

    # noinspection PyShadowingBuiltins
    def sorted(self, cmp=None, key=None, reverse=False):
        return self.__class__(sorted(self.iterator, cmp, key, reverse),
                              self.executor_class)

    def reversed(self):
        try:
            iterator = reversed(self.iterator)
        except TypeError:
            iterator = reversed(list(self.iterator))
        return self.__class__(iterator, self.executor_class)

    def peek(self, predicate):
        return self.__class__(peek(self.iterator, predicate),
                              self.executor_class)

    def limit(self, size):
        return self.__class__(islice(self.iterator, size), self.executor_class)

    def skip(self, size):
        return self.__class__(islice(self.iterator, size, None),
                              self.executor_class)

    def keys(self):
        return self.map(filter_keys)

    def values(self):
        return self.map(filter_values)

    def to_parallel(self, executor_class=ParallelExecutor):
        return self.__class__(self.iterator, executor_class)

    def to_process(self):
        return self.__class__(self.iterator, ProcessPoolExecutor)

    def to_sequental(self):
        return self.__class__(self.iterator, SequentalExecutor)

    # noinspection PyTypeChecker
    def largest(self, size):
        iterator = iter(self)
        heap = make_list(islice(iterator, size))
        heapify(heap)
        for item in iterator:
            if item > heap[0]:
                heapreplace(heap, item)
        return self.__class__(heap, self.executor_class)

    # noinspection PyTypeChecker
    def smallest(self, size):
        iterator = iter(self)
        heap = make_list(islice(iterator, size))
        _heapify_max(heap)
        for item in iterator:
            if item < heap[0]:
                _heappushpop_max(heap, item)
        return self.__class__(heap, self.executor_class)


# noinspection PyAttributeOutsideInit,PyAttributeOutsideInit,
# PyUnresolvedReferences
# noinspection PyAttributeOutsideInit,PyUnresolvedReferences
class StreamTerminalMixin(object):

    def reduce(self, function, initial=None):
        if initial is None:
            initial = next(self.iterator)
        return reduce_func(function, self.iterator, initial)

    def sum(self):
        iterator = accumulate(self.iterator, add)
        last = next(iterator)
        for item in iterator:
            last = item
        return last

    def count(self):
        if hasattr(self.iterator, "__len__"):
            # noinspection PyTypeChecker
            return len(self.iterator)
        return sum((1 for _ in self.iterator))

    def average(self):
        counter = 1
        total = next(self.iterator)
        for item in self.iterator:
            total = add(total, item)
            counter += 1
        return truediv(total, counter)

    def nth_element(self, nth):
        if nth == 1:
            return min(self.iterator)
        self.iterator = make_list(self.iterator)
        if nth <= len(self.iterator):
            return max(self.smallest(nth))

    def median(self):
        self.iterator = make_list(self.iterator)
        return self.nth_element(len(self.iterator) // 2)

    def any(self, predicate=None, parallel=False):
        if predicate is None:
            iterator = self.iterator
        else:
            iterator = self.map(predicate, parallel)
        return any(iterator)

    def all(self, predicate=None, parallel=False):
        if predicate is None:
            iterator = self.iterator
        else:
            iterator = self.map(predicate, parallel)
        return all(iterator)
