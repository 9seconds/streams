# -*- coding: utf-8 -*-


###############################################################################


from operator import add

from repoze.lru import LRUCache
from six import PY2, advance_iterator


###############################################################################


def distinct(iterable):
    distincts = set()
    for item in iterable:
        if item not in distincts:
            distincts.add(item)
            yield item


def partly_distinct(iterable):
    cache = LRUCache(10000)
    for item in iterable:
        if not cache.get(item):
            cache.put(item)
            yield item


def peek(iterable, function):
    for item in iterable:
        function(item)
        yield item


def seed(function, seed_value):
    yield seed_value
    while True:
        seed_value = function(seed_value)
        yield seed_value


if PY2:
    def accumulate(iterable, function=add):
        iterator = iter(iterable)
        total = advance_iterator(iterator)
        yield total
        for item in iterator:
            total = function(total, item)
            yield total
else:
    from itertools import accumulate
