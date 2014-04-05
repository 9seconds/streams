# -*- coding: utf-8 -*-


###############################################################################


from multiprocessing import cpu_count
from threading import RLock

from concurrent.futures import Executor

from six import text_type, string_types
# noinspection PyUnresolvedReferences
from six.moves import zip as izip

try:
    from cdecimal import Decimal
except ImportError:
    from decimal import Decimal


###############################################################################


def filter_keys(item):
    if isinstance(item, tuple):
        return item[0]
    return item


def filter_values(item):
    if isinstance(item, tuple):
        return item[-1]
    return item


def filter_true(argument):
    predicate, item = argument
    return bool(predicate(item)), item


def filter_false(argument):
    is_correct, item = filter_true(argument)
    return not is_correct, item


# noinspection PyBroadException
def int_or_none(item):
    if isinstance(item, int):
        return item
    try:
        return int(item)
    except:
        return None


# noinspection PyBroadException
def float_or_none(item):
    if isinstance(item, float):
        return item
    try:
        return float(item)
    except:
        return None


# noinspection PyBroadException
def long_or_none(item):
    if isinstance(item, long):
        return item
    try:
        return long(item)
    except:
        return None


# noinspection PyBroadException
def decimal_or_none(item):
    if isinstance(item, Decimal):
        return item
    try:
        return Decimal(item)
    except:
        return None


# noinspection PyBroadException
def unicode_or_none(item):
    if isinstance(item, text_type):
        return item
    try:
        return text_type(item)
    except:
        return None


# noinspection PyBroadException
def string_or_none(item):
    if isinstance(item, string_types):
        return item
    try:
        return str(item)
    except:
        return None


def apply_to_tuple(*funcs, **kwargs):
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
    predicate, item = argument
    item = item if isinstance(item, (tuple, list)) else (item, item)
    return apply_to_tuple(predicate, None, item=item)


def value_mapper(argument):
    predicate, item = argument
    item = item if isinstance(item, (tuple, list)) else (item, item)
    return apply_to_tuple(None, predicate, item=item)


def make_list(iterable):
    if isinstance(iterable, (list, tuple)):
        return iterable
    return list(iterable)


###############################################################################


class MaxHeapItem(object):

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
