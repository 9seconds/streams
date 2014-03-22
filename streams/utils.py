# -*- coding: utf-8 -*-


###############################################################################


from multiprocessing import cpu_count
from threading import RLock
from concurrent.futures import Executor

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


def filter_map(predicate):
    def map_function(item):
        return bool(predicate(item)), item
    return map_function


def not_predicate(predicate):
    def function(*args, **kwargs):
        return not predicate(*args, **kwargs)
    return function


def int_or_none(item):
    try:
        return int(item)
    except:
        return None


def float_or_none(item):
    try:
        return float(item)
    except:
        return None


def long_or_none(item):
    try:
        return long(item)
    except:
        return None


def decimal_or_none(item):
    try:
        return Decimal(item)
    except:
        return None


def key_mapper(predicate):
    def map_function(item):
        key, value = item if isinstance(item, tuple) else (item, item)
        return predicate(key), value
    return map_function


def value_mapper(predicate):
    def map_function(item):
        key, value = item if isinstance(item, tuple) else (item, item)
        return key, predicate(value)
    return map_function


def make_list(iterable):
    if isinstance(iterable, (list, tuple)):
        return iterable
    return list(iterable)


###############################################################################


class ExecutorPool(object):

    __slots__ = "lock", "instances"

    def __init__(self):
        self.lock = RLock()
        self.instances = {}

    def __del__(self):
        for instance in self.instances.itervalues():
            instance.shutdown()

    def __getitem__(self, item):
        if not issubclass(item, Executor):
            raise TypeError("Unknown type {}".format(item.__name__))

        name = item.__name__
        instance = self.instances.get(name)
        if instance:
            return instance

        with self.lock:
            instance = self.instances.get(name)
            if instance:
                return instance
            instance = item(cpu_count())
            self.instances[name] = instance
            return instance


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
