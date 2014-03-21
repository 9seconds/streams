# -*- coding: utf-8 -*-


###############################################################################


from operator import add

from six import PY2


###############################################################################


def distinct(iterable):
    distincts = set()
    for item in iterable:
        if item not in distincts:
            distincts.add(item)
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
        total = next(iterator)
        yield total
        for item in iterator:
            total = function(total, item)
            yield total
else:
    from itertools import accumulate
