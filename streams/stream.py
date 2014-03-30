# -*- coding: utf-8 -*-
"""
This module contains the definition of Stream class.
"""


###############################################################################


from __future__ import division

from collections import Iterable, Sized
from heapq import nlargest, nsmallest, heappush, heappop
from itertools import chain, islice, repeat
from operator import add, truediv
from re import compile as regex_compile

from six import iteritems, advance_iterator

# noinspection PyUnresolvedReferences
from six.moves import filter as ifilter, map as imap, reduce as reduce_func, \
    xrange as xxrange

from .iterators import seed, distinct, peek, accumulate, partly_distinct
from .poolofpools import PoolOfPools
from .utils import MaxHeapItem, filter_true, filter_false, value_mapper, \
    key_mapper, filter_keys, filter_values, make_list, int_or_none, \
    float_or_none, long_or_none, decimal_or_none, unicode_or_none


###############################################################################


class Stream(Iterable, Sized):
    """
    Stream class provides you with the basic functionality of Streams. Please
    checkout member documentation to get an examples.
    """

    WORKERS = PoolOfPools()
    SENTINEL = object()

    @classmethod
    def concat(cls, *streams):
        """
        Lazily concatenates several stream into one. The same as `Java 8
        concat <http://docs.oracle.com/javase/8/docs/api/java/util/stream/
        Stream.html#concat-java.util.stream.Stream-
        java.util.stream.Stream->`_.

        :param streams: The :py:class:`Stream` instances you want to
                        concatenate.
        :return: new processed :py:class:`Stream` instance.

        >>> stream1 = Stream(range(2))
        >>> stream2 = Stream(["2", "3", "4"])
        >>> stream3 = Stream([list(), dict()])
        >>> concatenated_stream = Stream.concat(stream1, stream2, stream3)
        >>> list(concatenated_stream)
        ... [0, 1, "2", "3", "4", [], {}]
        """
        return cls(streams).chain()

    @classmethod
    def iterate(cls, function, seed_value):
        """
        Returns seed stream. The same as for `Java 8 iterate
        <http://docs.oracle.com/javase/8/docs/api/java/util/stream/Stream.html
        #iterate-T-java.util.function.UnaryOperator->`_.

        Returns an infinite sequential ordered Stream produced by iterative
        application of a function ``f`` to an initial element seed, producing a
        Stream consisting of ``seed``, ``f(seed)``, ``f(f(seed))``, etc.

        The first element (position 0) in the Stream will be the provided
        seed. For ``n > 0``, the element at position n, will be the result of
        applying the function f to the element at position ``n - 1``.

        :param function function: The function to apply to the seed.
        :param object seed_value: The seed value of the function.
        :return: new processed :py:class:`Stream` instance.

        >>> stream = Stream.iterate(lambda value: value ** 2, 2)
        >>> iterator = iter(stream)
        >>> next(iterator)
        ... 2
        >>> next(iterator)
        ... 4
        >>> next(iterator)
        ... 8
        """
        return cls(seed(function, seed_value))

    @classmethod
    def range(cls, *args, **kwargs):
        """
        Creates numerial iterator. Absoultely the same as ``Stream.range(10)``
        and ``Stream(range(10))`` (in Python 2: ``Stream(xrange(10))``). All
        arguments go to :py:func:`range` (:py:func:`xrange`) directly.

        :return: new processed :py:class:`Stream` instance.

        >>> stream = Stream.range(6)
        >>> list(stream)
        ... [0, 1, 2, 3 ,4, 5]
        >>> stream = Stream.range(1, 6)
        >>> list(stream)
        ... [1, 2, 3, 4, 5]
        >>> stream = Stream.range(1, 6, 2)
        >>> list(stream)
        ... [1, 3, 5]
        """
        return cls(xxrange(*args, **kwargs))

    def __init__(self, iterator):
        """
        Initializes the :py:class:`Stream`.

        Actually it does some smart handling of iterator. If you give it an
        instance of :py:class:`dict` or its derivatives (such as
        :py:class:`collections.OrderedDict`), it will iterate through it's
        items (key and values). Otherwise just normal iterator would be used.

        :param Iterable iterator: Iterator which has to be converted into
                                  :py:class:`Stream`.
        """
        if isinstance(iterator, dict):
            self.iterator = iteritems(iterator)
        else:
            self.iterator = iter(iterator)

    # noinspection PyTypeChecker
    def __len__(self):
        """
        To support :py:func:`len` function if given iterator supports it.
        """
        return len(self.iterator)

    def __iter__(self):
        """
        To support iteration protocol.
        """
        return iter(self.iterator)

    def __reversed__(self):
        """
        To support :py:func:`reversed` iterator.
        """
        return self.reversed()

    @property
    def first(self):
        """
        Returns a first element from iterator and does not changes internals.

        >>> stream = Stream.range(10)
        >>> stream.first
        ... 0
        >>> stream.first
        ... 0
        >>> list(stream)
        ... [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        """
        first_element = advance_iterator(self.iterator)
        self.iterator = chain([first_element], self.iterator)
        return first_element

    def _filter(self, condition, predicate, **concurrency_kwargs):
        """
        Does parallel filtering on given ``condition`` with given
        `predicate``. Supports parallel execution.

        Internal method you do not want to use generally.
        """
        mapper = self.WORKERS.get(concurrency_kwargs)
        if mapper:
            iterator = ((predicate, item) for item in self)
            filtered = mapper(condition, iterator)
            filtered = (result for suitable, result in filtered if suitable)
        else:
            filtered = ifilter(predicate, self)
        return self.__class__(filtered)

    def filter(self, predicate, **concurrency_kwargs):
        """
        Does filtering according to the given ``predicate`` function. Also it
        supports parallelization (if predicate is pretty heavy function).

        You may consider it as equivalent of :py:func:`itertools.ifilter` but
        for stream with a possibility to parallelize this process.

        :param function predicate: Predicate for filtering elements of the
                                   :py:class:`Stream`.
        :param dict concurrency_kwargs: The same concurrency keywords as for
                                        :py:meth:`Stream.map`.
        :return: new processed :py:class:`Stream` instance.

        >>> stream = Stream.range(5)
        >>> stream = stream.filter(lambda item: item % 2 == 0)
        >>> list(stream)
        ... [0, 2, 4]
        """
        return self._filter(filter_true, predicate, **concurrency_kwargs)

    def exclude(self, predicate, **concurrency_kwargs):
        """
        Excludes items from :py:class:`Stream` according to the predicate.
        You can consider behaviour as the same as for
        :py:func:`itertools.ifilterfalse`.

        As :py:meth:`Stream.filter` it also supports parallelization. Please
        checkout :py:meth:`Stream.map` keyword arguments.

        :param function predicate: Predicate for filtering elements of the
                                   :py:class:`Stream`.
        :param dict concurrency_kwargs: The same concurrency keywords as for
                                        :py:meth:`Stream.map`.
        :return: new processed :py:class:`Stream` instance.

        >>> stream = Stream.range(6)
        >>> stream = stream.exclude(lambda item: item % 2 == 0)
        >>> list(stream)
        ... [1, 3, 5]
        """
        return self._filter(filter_false, predicate, **concurrency_kwargs)

    def regexp(self, regexp, flags=0):
        """
        Filters stream according to the regular expression using
        :py:func:`re.match`. It also supports the same flags as
        :py:func:`re.match`.

        :param str regexp: Regular expression for filtering.
        :param int flags: Flags from :py:mod:`re`.
        :return: new processed :py:class:`Stream` instance.

        >>> stream = Stream.range(100)
        >>> stream = stream.strings()
        >>> stream = stream.regexp(r"^1")
        >>> list(stream)
        ... ['1', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19']
        """
        regexp = regex_compile(regexp, flags)
        return self.filter(regexp.match)

    def divisible_by(self, number):
        """
        Filters stream for the numbers divisible by the given one.

        :param int number: Number which every element should be divisible by.
        :return: new processed :py:class:`Stream` instance.

        >>> stream = Stream.range(6)
        >>> stream = stream.divisible_by(2)
        >>> list(stream)
        ... [0, 2, 4]
        """
        return self.filter(lambda item: item % number == 0)

    def evens(self):
        """
        Filters and keeps only even numbers from the stream.

        :return: new processed :py:class:`Stream` instance.

        >>> stream = Stream.range(6)
        >>> stream = stream.evens()
        >>> list(stream)
        ... [0, 2, 4]
        """
        return self.divisible_by(2)

    def odds(self):
        """
        Filters and keeps only odd numbers from the stream.

        :return: new processed :py:class:`Stream` instance.

        >>> stream = Stream.range(6)
        >>> stream = stream.odds()
        >>> list(stream)
        ... [1, 3, 5]
        """
        return self.filter(lambda item: item % 2 != 0)

    def instances_of(self, cls):
        """
        Filters and keeps only instances of the given class.

        :param class cls: Class for filtering.
        :return: new processed :py:class:`Stream` instance.

        >>> int_stream = Stream.range(4)
        >>> str_stream = Stream.range(4).strings()
        >>> result_stream = Stream.concat(int_stream, str_stream)
        >>> result_stream = result_stream.instances_of(str)
        >>> list(result_stream)
        ... ['0', '1',  '2', '3']
        """
        return self.filter(lambda item: isinstance(item, cls))

    def exclude_nones(self):
        """
        Excludes ``None`` from the stream.

        :return: new processed :py:class:`Stream` instance.

        >>> stream = Stream([1, 2, None, 3, None, 4])
        >>> stream = stream.exclude_nones()
        >>> list(stream)
        ... [1, 2, 3, 4]
        """
        return self.filter(lambda item: item is not None)

    def only_nones(self):
        """
        Keeps only ``None`` in the stream (for example, for counting).

        :return: new processed :py:class:`Stream` instance.

        >>> stream = Stream([1, 2, None, 3, None, 4])
        >>> stream = stream.only_nones()
        >>> list(stream)
        ... [None, None]
        """
        return self.filter(lambda item: item is None)

    def only_trues(self):
        """
        Keeps only those elements where ``bool(element) == True``.

        :return: new processed :py:class:`Stream` instance.

        >>> stream = Stream([1, 2, None, 0, {}, [], 3])
        >>> stream = stream.only_trues()
        >>> list(stream)
        ... [1, 2, 3]
        """
        return self.filter(bool)

    def only_falses(self):
        """
        Keeps only those elements where ``bool(item) == False``.

        :return: new processed :py:class:`Stream` instance.

        >>> stream = Stream([1, 2, None, 0, {}, [], 3])
        >>> stream = stream.only_trues()
        >>> list(stream)
        ... [None, 0, {}, []]

        Opposite to :py:meth:`Stream.only_trues`.
        """
        return self.filter(lambda item: not bool(item))

    def ints(self):
        """
        Tries to convert everything to :py:func:`int` and keeps only
        successful attempts.

        :return: new processed :py:class:`Stream` instance.

        >>> stream = Stream([1, 2, "3", "4", None, {}, 5])
        >>> stream = stream.ints()
        >>> list(stream)
        ... [1, 2, 3, 4, 5]

        .. note::
            It is not the same as ``stream.map(int)`` because it removes failed
            attempts.
        """
        return self.map(int_or_none).exclude_nones()

    def floats(self):
        """
        Tries to convert everything to :py:func:`float` and keeps only
        successful attempts.

        :return: new processed :py:class:`Stream` instance.

        >>> stream = Stream([1, 2, "3", "4", None, {}, 5])
        >>> stream = stream.floats()
        >>> list(stream)
        ... [1.0, 2.0, 3.0, 4.0, 5.0]

        .. note::
            It is not the same as ``stream.map(float)`` because it removes
            failed attempts.
        """
        return self.map(float_or_none).exclude_nones()

    def longs(self):
        """
        Tries to convert everything to :py:func:`long` and keeps only
        successful attempts.

        :return: new processed :py:class:`Stream` instance.

        >>> stream = Stream([1, 2, "3", "4", None, {}, 5])
        >>> stream = stream.longs()
        >>> list(stream)
        ... [1L, 2L, 3L, 4L, 5L]

        .. note::
            It is not the same as ``stream.map(long)`` because it removes
            failed attempts.
        """
        return self.map(long_or_none).exclude_nones()

    def decimals(self):
        """
        Tries to convert everything to :py:class:`decimal.Decimal` and keeps
        only successful attempts.

        :return: new processed :py:class:`Stream` instance.

        >>> stream = Stream([1, 2.0, "3", "4.0", None, {}])
        >>> stream = stream.longs()
        >>> list(stream)
        ... [Decimal('1'), Decimal('2'), Decimal('3'), Decimal('4.0')]

        .. note::
            It is not the same as ``stream.map(Decimal)`` because it removes
            failed attempts.

        .. note::
            It tries to use ``cdecimal`` module if possible.
        """
        return self.map(decimal_or_none).exclude_nones()

    def strings(self):
        """
        Tries to convert everything to :py:func:`unicode` (:py:class:`str`
        for Python 3) and keeps only successful attempts.

        :return: new processed :py:class:`Stream` instance.

        >>> stream = Stream([1, 2.0, "3", "4.0", None, {}])
        >>> stream = stream.strings()
        >>> list(stream)
        ... ['1', '2.0', '3', '4.0', 'None', '{}']

        .. note::
            It is not the same as ``stream.map(str)`` because it removes
            failed attempts.

        .. note::
            It tries to convert to :py:class:`unicode` if possible,
            not :py:class:`bytes`.
        """
        return self.map(unicode_or_none).exclude_nones()

    def tuplify(self, clones=2):
        """
        Tuplifies iterator. Creates a tuple from iterable with ``clones``
        elements.

        :param int clones: The count of elements in result tuple.
        :return: new processed :py:class:`Stream` instance.

        >>> stream = Stream.range(2)
        >>> stream = stream.tuplify(3)
        >>> list(stream)
        ... [(0, 0, 0), (1, 1, 1)]
        """
        return self.__class__(tuple(repeat(item, clones)) for item in self)

    def map(self, predicate, **concurrency_kwargs):
        """
        The corner method of the :py:class:`Stream` and others are basing on
        it. It supports parallelization out of box. Actually it works just like
        :py:func:`itertools.imap`.

        :param function predicate: Predicate to map each element of the
                                   :py:class:`Stream`.
        :param dict concurrency_kwargs: The same concurrency keywords.
        :return: new processed :py:class:`Stream` instance.

        Parallelization is configurable by keywords. There is 2 keywords
        supported: ``parallel`` and ``process``. If you set one keyword to
        ``True`` then :py:class:`Stream` would try to map everything
        concurrently. If you want more intelligent tuning just set the number
        of workers you want.

        For example, you have a list of URLs to fetch

        >>> stream = Stream(urls)

        You can fetch them in parallel

        >>> stream.map(requests.get, parallel=True)

        By default, the number of workers is the number of cores on your
        computer. But if you want to have 64 workers, you are free to do it

        >>> stream.map(requests.get, parallel=64)

        The same for ``process`` which will try to use processes.

        >>> stream.map(requests.get, process=True)

        and

        >>> stream.map(requests.get, process=64)

        .. note::
            Python multiprocessing has its caveats and pitfalls, please use
            it carefully (especially ``predicate``). Read the documentation on
            :py:mod:`multiprocessing` and try to google best practices.

        .. note::
            If you set both ``parallel`` and ``process`` keywords only
            ``parallel`` would be used. If you want to disable some type of
            concurrency just set it to ``None``.

            >>> stream.map(requests.get, parallel=None, process=64)

            is equal to

            >>> stream.map(requests.get, process=64)

            The same for ``parallel``

            >>> stream.map(requests.get, parallel=True, process=None)

            is equal to

            >>> stream.map(requests.get, parallel=True)

        .. note::
            By default no concurrency is used.
        """
        mapper = self.WORKERS.get(concurrency_kwargs)
        if not mapper:
            mapper = imap
        return self.__class__(mapper(predicate, self))

    def _kv_map(self, mapper, predicate, **concurrency_kwargs):
        """
        Internal method for :py:meth:`Stream.value_map` and
        :py:meth:`Stream.key_map`. Do not use it outside.
        """
        iterator = ((predicate, item) for item in self)
        stream = self.__class__(iterator)
        return stream.map(mapper, **concurrency_kwargs)

    def value_map(self, predicate, **concurrency_kwargs):
        """
        Maps only value in (key, value) pair. If element is single one, then
        it would be :py:meth:`Stream.tuplify` first.

        :param function predicate: Predicate to apply to the value of element
                                   in the :py:class:`Stream`.
        :param dict concurrency_kwargs: The same concurrency keywords as for
                                        :py:meth:`Stream.map`.
        :return: new processed :py:class:`Stream` instance.

        >>> stream = Stream.range(4)
        >>> stream = stream.tuplify()
        >>> stream = stream.value_map(lambda item: item ** 3)
        >>> list(stream)
        ... [(0, 0), (1, 1), (2, 8), (3, 27)]
        >>> stream = Stream.range(4)
        >>> stream = stream.value_map(lambda item: item ** 3)
        >>> list(stream)
        ... [(0, 0), (1, 1), (2, 8), (3, 27)]
        """
        return self._kv_map(value_mapper, predicate, **concurrency_kwargs)

    def key_map(self, predicate, **concurrency_kwargs):
        """
        Maps only key in (key, value) pair. If element is single one, then
        it would be :py:meth:`Stream.tuplify` first.

        :param function predicate: Predicate to apply to the key of element in
                                   the :py:class:`Stream`.
        :param dict concurrency_kwargs: The same concurrency keywords as for
                                        :py:meth:`Stream.map`.
        :return: new processed :py:class:`Stream` instance.

        >>> stream = Stream.range(4)
        >>> stream = stream.tuplify()
        >>> stream = stream.key_map(lambda item: item ** 3)
        >>> list(stream)
        ... [(0, 0), (1, 1), (8, 2), (27, 3)]
        >>> stream = Stream.range(4)
        >>> stream = stream.key_map(lambda item: item ** 3)
        >>> list(stream)
        ... [(0, 0), (1, 1), (8, 2), (27, 3)]
        """
        return self._kv_map(key_mapper, predicate, **concurrency_kwargs)

    def distinct(self):
        """
        Removes duplicates from the stream.

        :return: new processed :py:class:`Stream` instance.

        .. note::
            All objects in the stream have to be hashable (support
            :py:meth:`__hash__`).

        .. note::
            Please use it carefully. It returns new :py:class:`Stream` but will
            keep every element in your memory.
        """
        return self.__class__(distinct(self))

    def partly_distinct(self):
        """
        Excludes some duplicates from the memory.

        :return: new processed :py:class:`Stream` instance.

        .. note::
            All objects in the stream have to be hashable (support
            :py:meth:`__hash__`).

        .. note::
            It won't guarantee you that all duplicates will be removed
            especially if your stream is pretty big and cardinallity is huge.
        """
        return self.__class__(partly_distinct(self))

    def sorted(self, key=None, reverse=False):
        """
        Sorts the stream elements.

        :param function key: Key function for sorting
        :param bool reverse: Do we need to sort in descending order?
        :return: new processed :py:class:`Stream` instance.

        ... note::
            Of course no magic here, we need to fetch all elements for sorting
            into the memory.
        """
        return self.__class__(sorted(self, reverse=reverse, key=key))

    def reversed(self):
        """
        Reverses the stream.

        :return: new processed :py:class:`Stream` instance.

        ... note::
            If underlying iterator won't support reversing, we are in trouble
            and need to fetch everything into the memory.
        """
        try:
            iterator = reversed(self.iterator)
        except TypeError:
            iterator = reversed(list(self.iterator))
        return self.__class__(iterator)

    def peek(self, predicate):
        """
        Does the same as `Java 8 peek <http://docs.oracle.com/javase/8/docs/
        api/java/util/stream/Stream.html#peek-java.util.function.Consumer->`_.

        :param function predicate: Predicate to apply on each element.
        :return: new processed :py:class:`Stream` instance.

        Returns a stream consisting of the elements of this stream,
        additionally performing the provided action on each element as
        elements are consumed from the resulting stream.
        """
        return self.__class__(peek(self, predicate))

    def limit(self, size):
        """
        Limits stream to given ``size``.

        :param int size: The size of new :py:class:`Stream`.
        :return: new processed :py:class:`Stream` instance.

        >>> stream = Stream.range(1000)
        >>> stream = stream.limit(5)
        >>> list(stream)
        ... [0, 1, 2, 3, 4]
        """
        return self.__class__(islice(self, size))

    def skip(self, size):
        """
        Skips first ``size`` elements.

        :param int size: The amount of elements to skip.
        :return: new processed :py:class:`Stream` instance.

        >>> stream = Stream.range(10)
        >>> stream = stream.skip(5)
        >>> list(stream)
        ... [5, 6, 7, 8, 9]
        """
        return self.__class__(islice(self, size, None))

    def keys(self):
        """
        Iterates only keys from the stream (first element from the
        :py:class:`tuple`). If element is single then it will be used.

        :return: new processed :py:class:`Stream` instance.

        >>> stream = Stream.range(5)
        >>> stream = stream.key_map(lambda item: item ** 3)
        >>> stream = stream.keys()
        >>> list(stream)
        ... [0, 1, 8, 27, 64]
        """
        return self.map(filter_keys)

    def values(self):
        """
        Iterates only values from the stream (last element from the
        :py:class:`tuple`). If element is single then it will be used.

        :return: new processed :py:class:`Stream` instance.

        >>> stream = Stream.range(5)
        >>> stream = stream.key_map(lambda item: item ** 3)
        >>> stream = stream.values()
        >>> list(stream)
        ... [0, 1, 2, 3, 4]
        """
        return self.map(filter_values)

    def chain(self):
        """
        If elements of the stream are iterable, tries to flat that stream.

        :return: new processed :py:class:`Stream` instance.

        >>> stream = Stream.range(3)
        >>> stream = stream.tuplify()
        >>> stream = stream.chain()
        >>> list(stream)
        >>> [0, 0, 1, 1, 2, 2]
        """
        return self.__class__(chain.from_iterable(self))

    def largest(self, size):
        """
        Returns ``size`` largest elements from the stream.

        :return: new processed :py:class:`Stream` instance.

        >>> stream = Stream.range(3000)
        >>> stream.largest(5)
        >>> list(stream)
        >>> [2999, 2998, 2997, 2996, 2995]
        """
        return self.__class__(nlargest(size, self))

    def smallest(self, size):
        """
        Returns ``size`` largest elements from the stream.

        :return: new processed :py:class:`Stream` instance.

        >>> stream = Stream.range(3000)
        >>> stream.smallest(5)
        >>> list(stream)
        >>> [0, 1, 2, 3, 4]
        """
        return self.__class__(nsmallest(size, self))

    def reduce(self, function, initial=SENTINEL):
        """
        Applies :py:func:`reduce` for the iterator

        :param function function: Reduce function
        :param object initial: Initial value (if nothing set, first element)
                               would be used.

        >>> Stream = stream.range(5)
        >>> stream.reduce(operator.add)
        ... 10
        """
        iterator = iter(self)
        if initial is self.SENTINEL:
            initial = advance_iterator(iterator)
        return reduce_func(function, iterator, initial)

    def sum(self):
        """
        Returns the sum of elements in the stream.

        >>> Stream = stream.range(10)
        >>> stream = stream.decimals()
        >>> stream = stream.sum()
        ... Decimal('45')

        .. note::
            Do not use :py:func:`sum` here. It does sum regarding to defined
            :py:meth:`__add__` of the classes. So it can sum
            :py:class:`decimal.Decimal` with :py:class:`int` for example.
        """
        iterator = accumulate(self, add)
        last = advance_iterator(iterator)
        for item in iterator:
            last = item
        return last

    def count(self, element=SENTINEL):
        """
        Returns the number of elements in the stream. If ``element`` is set,
        returns the count of particular element in the stream.

        :param object element: The element we need to count in the stream
        :return: The number of elements of the count of particular element.
        """
        if element is not self.SENTINEL:
            return sum((1 for item in self if item is element))
        if hasattr(self.iterator, "__len__"):
            # noinspection PyTypeChecker
            return len(self.iterator)
        return sum((1 for _ in self))

    def average(self):
        """
        Calculates the average of elements in the stream.

        :return: The average of elements.

        >>> stream = Stream.range(10000)
        >>> stream.average()
        ... 4999.5
        """
        counter = 1
        iterator = iter(self)
        total = advance_iterator(iterator)
        for item in iterator:
            total = add(total, item)
            counter += 1
        return truediv(total, counter)

    def nth(self, nth_element):
        """
        Returns Nth element from the stream.

        :param int nth_element: Number of element to return.
        :return: Nth element.

        >>> stream = Stream.range(10000)
        >>> stream.average()
        ... 4999.5

        .. note::
            Please be noticed that all elements from the stream would be
            fetched in the memory (except of the case where
            ``nth_element == 1``).
        """
        if nth_element == 1:
            return min(self)
        self.iterator = make_list(self.iterator)
        if nth_element <= len(self.iterator):
            return max(self.smallest(nth_element))

    def median(self):
        """
        Returns median value from the stream.

        :return: The median of the stream.

        >>> stream = Stream.range(10000)
        >>> stream.median()
        ... 5000

        .. note::
            Please be noticed that all elements from the stream would be
            fetched in the memory.
        """
        biggest, smallest = [], []
        iterator = iter(self)
        first_elements = list(islice(iterator, 2))
        if not first_elements:
            return None
        if len(first_elements) == 1:
            return first_elements[0]

        first, last = first_elements
        if first > last:
            first, last = last, first
        smallest.append(MaxHeapItem(first))
        biggest.append(last)

        for item in iterator:
            if item < smallest[0].value:
                heappush(smallest, MaxHeapItem(item))
            else:
                heappush(biggest, item)
            if len(smallest) > len(biggest) + 1:
                heappush(biggest, heappop(smallest).value)
            elif len(biggest) > len(smallest) + 1:
                heappush(smallest, MaxHeapItem(heappop(biggest)))

        biggest_item = max(biggest, smallest, key=len)[0]
        if isinstance(biggest_item, MaxHeapItem):
            return biggest_item.value
        return biggest_item

    def any(self, predicate=bool, **concurrency_kwargs):
        """
        Check if any element matching given ``predicate`` exists in the stream.
        If ``predicate`` is not defined, :py:func:`bool` is used.

        :param function predicate: Predicate to apply to each element of the
                                   :py:class:`Stream`.
        :param dict concurrency_kwargs: The same concurrency keywords as for
                                        :py:meth:`Stream.map`.
        :return: The result if we have matched elements or not.

        >>> stream = Stream.range(5)
        >>> stream.any(lambda item: item < 100)
        ... True
        """
        if predicate is None:
            iterator = iter(self)
        else:
            iterator = self.map(predicate, **concurrency_kwargs)
        return any(iterator)

    def all(self, predicate=bool, **concurrency_kwargs):
        """
        Check if all elements matching given ``predicate`` exist in the stream.
        If ``predicate`` is not defined, :py:func:`bool` is used.

        :param function predicate: Predicate to apply to each element of the
                                   :py:class:`Stream`.
        :param dict concurrency_kwargs: The same concurrency keywords as for
                                        :py:meth:`Stream.map`.
        :return: The result if we have matched elements or not.

        >>> stream = Stream.range(5)
        >>> stream.all(lambda item: item > 100)
        ... False
        """
        if predicate is None:
            iterator = iter(self)
        else:
            iterator = self.map(predicate, **concurrency_kwargs)
        return all(iterator)
