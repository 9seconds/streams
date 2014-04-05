# -*- coding: utf-8 -*-
"""
This module contains some useful iterators. Consider it as a small ad-hoc
extension pack for :py:mod:`itertools`.
"""


###############################################################################


from operator import add
from sys import version_info

from repoze.lru import LRUCache
from six import advance_iterator


###############################################################################


def distinct(iterable):
    """
    Filters items from iterable and returns only distinct ones. Keeps order.

    :param Iterable iterable: Something iterable we have to filter.

    >>> list(distinct([1, 2, 3, 2, 1, 2, 3, 4]))
    ... [1, 2, 3, 4]

    .. note::
        This is fair implementation and we have to **keep all items in
        memory**.

    .. note::
        All items have to be hashable.
    """
    distincts = set()
    for item in iterable:
        if item not in distincts:
            distincts.add(item)
            yield item


def partly_distinct(iterable):
    """
    Filters items from iterable and **tries to return only distincts**.
    Keeps order.

    :param Iterable iterable: Something iterable we have to filter.

    >>> list(partly_distinct([1, 2, 3, 2, 1, 2, 3, 4]))
    ... [1, 2, 3, 4]

    .. note::
        Unlike :py:func:`distinct` it won't guarantee that all elements would
        be distinct. But if you have rather small cardinality of the stream,
        this would work.

    .. note::
        Current implementation guarantees support for 10000 distinct values.
        If your cardinality is bigger, there might be some duplicates.
    """
    cache = LRUCache(10000)
    for item in iterable:
        if not cache.get(item):
            cache.put(item, True)
            yield item


def peek(iterable, function):
    """
    Does the same as `Java 8 peek <http://docs.oracle.com/javase/8/docs/
    api/java/util/stream/Stream.html#peek-java.util.function.Consumer->`_
    does.

    :param Iterable iterable: Iterable we want to peek
    :param function function: Peek function

    >>> def peek_func(item):
    ...     print "peek", item
    >>> list(peek([1, 2, 3], peek_func))
    ... peek 1
    ... peek 2
    ... peek 3
    ... [1, 2, 3]
    """
    for item in iterable:
        function(item)
        yield item


def seed(function, seed_value):
    """
    Does the same as `Java 8 iterate
    <http://docs.oracle.com/javase/8/docs/api/java/util/stream/Stream.html
    #iterate-T-java.util.function.UnaryOperator->`_.

    :param Iterable iterable: Iterable we want to peek
    :param function function: Peek function

    >>> iterator = seed(lambda x: x * 10, 1)
    >>> next(iterator)
    ... 1
    >>> next(iterator)
    ... 10
    >>> next(iterator)
    ... 100
    """
    yield seed_value
    while True:
        seed_value = function(seed_value)
        yield seed_value


if version_info < (3, 3):
    def accumulate(iterable, function=add):
        """
        Implementation of :py:func:`itertools.accumulate` from Python 3.3.
        """
        iterator = iter(iterable)
        total = advance_iterator(iterator)
        yield total
        for item in iterator:
            total = function(total, item)
            yield total
else:
    # noinspection PyUnresolvedReferences
    from itertools import accumulate
