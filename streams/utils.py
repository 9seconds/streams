# -*- coding: utf-8 -*-


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
