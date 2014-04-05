# -*- coding: utf-8 -*-
"""
This module contains some utility functions for Streams.

You may wonder why do we need for such simple ``filter-*`` functions. The
reason is simple and this is about how :py:mod:`multiprocessing` and therefore
:py:class:`concurrent.futures.ProcessPoolExecutor` works. It can't pickle
lambdas so we need for whole pickleable functions.
"""


###############################################################################


from six import text_type
# noinspection PyUnresolvedReferences
from six.moves import zip as izip

try:
    from cdecimal import Decimal
except ImportError:
    from decimal import Decimal


###############################################################################


def filter_keys(item):
    """
    Returns first element of the tuple or ``item`` itself.

    :param object item: It can be tuple, list or just an object.

    >>> filter_keys(1)
    ... 1
    >>> filter_keys((1, 2))
    ... 1
    """
    if isinstance(item, tuple):
        return item[0]
    return item


def filter_values(item):
    """
    Returns last element of the tuple or ``item`` itself.

    :param object item: It can be tuple, list or just an object.

    >>> filter_values(1)
    ... 1
    >>> filter_values((1, 2))
    ... 2
    """
    if isinstance(item, tuple):
        return item[-1]
    return item


def filter_true(argument):
    """
    Return the predicate value of given item and the item itself.

    :param tuple argument: Argument consists of predicate function and item
                           iteself.

    >>> filter_true((lambda x: x <= 5, 5))
    ... True, 5
    >>> filter_true((lambda x: x > 100, 1)
    ... False, 1
    """
    predicate, item = argument
    return bool(predicate(item)), item


def filter_false(argument):
    """
    Opposite to :py:func:`streams.utils.filter_true`

    :param tuple argument: Argument consists of predicate function and item
                           iteself.

    >>> filter_false((lambda x: x <= 5, 5))
    ... False, 5
    >>> filter_false((lambda x: x > 100, 1))
    ... True, 1
    """
    is_correct, item = filter_true(argument)
    return not is_correct, item


# noinspection PyBroadException
def int_or_none(item):
    """
    Tries to convert ``item`` to :py:func:`int`. If it is not possible, returns
    ``None``.

    :param object item: Element to convert into :py:func:`int`.

    >>> int_or_none(1)
    ... 1
    >>> int_or_none("1")
    ... 1
    >>> int_or_none("smth")
    ... None
    """
    if isinstance(item, int):
        return item
    try:
        return int(item)
    except:
        return None


# noinspection PyBroadException
def float_or_none(item):
    """
    Tries to convert ``item`` to :py:func:`float`. If it is not possible,
    returns ``None``.

    :param object item: Element to convert into :py:func:`float`.

    >>> float_or_none(1)
    ... 1.0
    >>> float_or_none("1")
    ... 1.0
    >>> float_or_none("smth")
    ... None
    """
    if isinstance(item, float):
        return item
    try:
        return float(item)
    except:
        return None


# noinspection PyBroadException
def long_or_none(item):
    """
    Tries to convert ``item`` to :py:func:`long`. If it is not possible,
    returns ``None``.

    :param object item: Element to convert into :py:func:`long`.

    >>> long_or_none(1)
    ... 1L
    >>> long_or_none("1")
    ... 1L
    >>> long_or_none("smth")
    ... None
    """
    if isinstance(item, long):
        return item
    try:
        return long(item)
    except:
        return None


# noinspection PyBroadException
def decimal_or_none(item):
    """
    Tries to convert ``item`` to :py:class:`decimal.Decimal`. If it is not
    possible, returns ``None``.

    :param object item: Element to convert into :py:class:`decimal.Decimal`.

    >>> decimal_or_none(1)
    ... Decimal("1")
    >>> decimal_or_none("1")
    ... Decimal("1")
    >>> decimal_or_none("smth")
    ... None
    """
    if isinstance(item, Decimal):
        return item
    try:
        return Decimal(item)
    except:
        return None


# noinspection PyBroadException
def unicode_or_none(item):
    """
    Tries to convert ``item`` to :py:func:`unicode`. If it is not possible,
    returns ``None``.

    :param object item: Element to convert into :py:func:`unicode`.

    >>> unicode_or_none(1)
    ... u"1"
    >>> unicode_or_none("1")
    ... u"1"
    >>> unicode_or_none("smth")
    ... u"smth"

    .. note::
        This is relevant for Python 2 only. Python 3 will use native
        :py:func:`str`.
    """
    if isinstance(item, text_type):
        return item
    try:
        return text_type(item)
    except:
        return None


def apply_to_tuple(*funcs, **kwargs):
    """
    Applies several functions to one ``item`` and returns tuple of results.

    :param list func:  The list of functions we need to apply.
    :param dict kwargs: Keyword arguments with only one mandatory argument,
                        ``item``. Functions would be applied to this item.

    >>> apply_to_tuple(int, float, item="1")
    ... (1, 1.0)
    """
    item = kwargs["item"]
    if not isinstance(item, (tuple, list)):
        return funcs[0](item)

    result = []
    for func, arg in izip(funcs, item):
        if func is not None:
            arg = func(arg)
        result.append(arg)
    return tuple(result)


def key_mapper(argument):
    """
    Maps ``predicate`` only to key (first element) of a ``item``. If ``item``
    is not :py:func:`tuple` then tuplifies it first.

    :param tuple argument: The tuple of (``predicate`` and ``item``).

    >>> key_mapper((lambda x: x + 10, (1, 2)))
    ... (11, 2)
    """
    predicate, item = argument
    item = item if isinstance(item, (tuple, list)) else (item, item)
    return apply_to_tuple(predicate, None, item=item)


def value_mapper(argument):
    """
    Maps ``predicate`` only to value (last element) of a ``item``. If ``item``
    is not :py:func:`tuple` then tuplifies it first.

    :param tuple argument: The tuple of (``predicate`` and ``item``).

    >>> value_mapper((lambda x: x + 10, (1, 2)))
    ... (1, 12)
    """
    predicate, item = argument
    item = item if isinstance(item, (tuple, list)) else (item, item)
    return apply_to_tuple(None, predicate, item=item)


def make_list(iterable):
    """
    Makes a list from given ``iterable``. But won't create new one if
    ``iterable`` is a :py:func:`list` or :py:func:`tuple` itself.

    :param Iterable iterable: Some iterable entity we need to convert into
                              :py:func:`list`.
    """
    if isinstance(iterable, (list, tuple)):
        return iterable
    return list(iterable)


###############################################################################


class MaxHeapItem(object):
    """
    This is small wrapper around item to give it a possibility to use heaps
    from :py:mod:`heapq` as max-heaps. Unfortunately this module provides
    min-heaps only.

    Guys, come on. We need for max-heaps to.
    """

    __slots__ = "value",

    def __init__(self, value):
        self.value = value

    def __lt__(self, other):
        other = other.value if isinstance(other, MaxHeapItem) else other
        return self.value > other

    def __le__(self, other):
        other = other.value if isinstance(other, MaxHeapItem) else other
        return self.value >= other.value

    def __gt__(self, other):
        other = other.value if isinstance(other, MaxHeapItem) else other
        return self.value < other

    def __ge__(self, other):
        other = other.value if isinstance(other, MaxHeapItem) else other
        return self.value <= other

    def __eq__(self, other):
        other = other.value if isinstance(other, MaxHeapItem) else other
        return self.value == other

    def __ne__(self, other):
        other = other.value if isinstance(other, MaxHeapItem) else other
        return self.value != other

    def __cmp__(self, other):
        other = other.value if isinstance(other, MaxHeapItem) else other
        if self.value < other:
            return 1
        if self.value == other:
            return 0
        return -1

    def __repr__(self):
        return repr(self.value)

    def __hash__(self):
        return hash(self.value)

    def __nonzero__(self):
        return bool(self.value)
