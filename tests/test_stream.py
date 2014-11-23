# -*- coding: utf-8 -*-


###############################################################################

from itertools import chain
from operator import add, itemgetter
from random import shuffle

try:
    from cdecimal import Decimal
except ImportError:
    from decimal import Decimal
try:
    from unittest2 import TestCase
except ImportError:
    from unittest import TestCase

# noinspection PyUnresolvedReferences
from six.moves import xrange
from six import string_types, text_type
from six import PY3
if PY3:
    long = int

from streams import Stream


###############################################################################
class StreamTests(TestCase):
    def test_no_cache(self):
        # Make a normal stream.
        stream = Stream.range(10)
        # Iterate once
        self.assertEqual(list(stream), list(range(10)))
        # Iterate twice
        self.assertEqual(list(stream), [])

    def test_cache(self):
        # Make a cached stream.
        stream = Stream.range(10).cache()
        # Iterate once
        self.assertEqual(list(stream), list(range(10)))
        # Iterate twice, this time from the cache.
        self.assertEqual(list(stream), list(range(10)))

        # Now, we make a new, smaller, cached stream fromm our cached stream.
        stream = stream.cache(5)
        # Iterate once
        self.assertEqual(list(stream), list(range(10)))
        # Iterate twice, this time from the cache. We get the last 5 values.
        self.assertEqual(list(stream), list(range(5, 10)))

    #   Stream class methods
    def test_it_should_produce_a_range(self):
        stream = Stream.range(10)
        self.assertIsInstance(stream, Stream)
        self.assertEqual(list(stream), list(range(10)))

    def test_it_should_concatenate_iterables(self):
        stream = Stream.concat(Stream.range(10), Stream.range(10))
        self.assertListEqual(list(stream), list(xrange(10)) + list(xrange(10)))

        stream = Stream.concat(xrange(10), xrange(10), xrange(10))
        self.assertListEqual(list(stream.distinct()), list(xrange(10)))

        stream = Stream.concat(xrange(10), xrange(10), xrange(10))
        self.assertEqual(stream.count(), 30)

    def test_it_should_iterate_on_a_seed_value(self):
        i = iter(Stream.iterate(lambda x: x * 10, 1))
        self.assertEqual(next(i), 1)
        self.assertEqual(next(i), 10)
        self.assertEqual(next(i), 100)
        self.assertEqual(next(i), 1000)

    #   Stream exhaustion tests
    def test_it_should_iterate_over_an_iterable(self):
        stream = Stream.range(10)
        self.assertListEqual(list(stream), list(xrange(10)))

    def test_it_should_iterate_over_an_iterable_multiple_times(self):
        stream = Stream.range(10)
        self.assertListEqual(list(stream), list(xrange(10)))
        self.assertListEqual(list(stream), [])

    #   stream.all()
    def test_all(self):
        self.assertTrue(Stream(xrange(1, 10)).all(parallel=True))
        self.assertTrue(Stream(xrange(1, 10)).all())
        self.assertTrue(Stream([]).all())
        self.assertTrue(Stream([]).all())
        self.assertFalse(Stream(xrange(10)).all(parallel=True))
        self.assertFalse(Stream(xrange(10)).all())
        self.assertFalse(Stream(xrange(10)).all(lambda item: item < 5))
        self.assertTrue(Stream(xrange(10)).all(lambda item: item < 100))

    #   stream.any()
    def test_any(self):
        self.assertTrue(Stream(xrange(10)).any())
        self.assertFalse(Stream([]).any())
        self.assertTrue(Stream(xrange(10)).any(lambda item: item > 5,
                                               parallel=True))
        self.assertTrue(Stream(xrange(10)).any(lambda item: item > 5))
        self.assertFalse(Stream(xrange(10)).any(lambda item: item < -1,
                                                parallel=True))

    #   stream.average()
    def test_average(self):
        self.assertAlmostEqual(Stream(xrange(200)).average(), 99.5)

    #   stream.chain()
    def test_it_should_chain_iterables_together(self):
        stream = Stream((range(10), range(10)))
        self.assertListEqual(list(stream.chain()),
                             list(xrange(10)) + list(xrange(10)))

    #   stream.count()
    def test_it_should_count_the_number_of_items_in_the_stream(self):
        stream = Stream.range(100)
        self.assertEqual(stream.count(), 100)

    def test_it_should_count_the_number_of_occurrences_in_the_stream(self):
        stream = Stream(xrange(100))
        stream = stream.limit(50)
        self.assertEqual(stream.count(), 50)

        stream = Stream(xrange(100))
        stream = stream.limit(1000)
        self.assertEqual(stream.count(), 100)

    #   stream.divisible by()
    def test_it_should_filter_by_divisibility(self):
        stream = Stream(range(6))
        stream = stream.divisible_by(2)
        self.assertListEqual(list(stream), [0, 2, 4])

        stream = Stream(xrange(2000))
        stream = stream.ints().divisible_by(10)
        self.assertEqual(stream.count(), 200)

        stream = Stream(xrange(2000))
        stream = stream.divisible_by(1000)
        self.assertEquals(list(stream), [0, 1000])

    #   stream.decimals()
    def test_it_should_cast_a_stream_to_decimals(self):
        items = list(xrange(10)) + ['0', '23', '99', 'foo', None]
        stream = Stream(items)
        decimals = stream.decimals()
        self.assertListEqual(list(decimals), [Decimal(i) for i in items[0:-2]])

    #   stream.distinct()
    def test_it_should_remove_repeated_items_from_the_stream(self):
        elements = chain(xrange(10), xrange(10), xrange(10), xrange(20))
        stream = Stream(elements)
        self.assertListEqual(list(stream.distinct()), list(xrange(20)))

    #   stream.evens()
    def test_it_should_filter_evens(self):
        stream = Stream(range(6))
        stream = stream.evens()
        self.assertListEqual(list(stream), [0, 2, 4])

        stream = Stream(xrange(200))
        stream = stream.ints().evens()
        elements = list(stream)
        self.assertEqual(len(elements), 100)
        self.assertTrue(all(item % 2 == 0 for item in elements))

    #   stream.exclude()
    def test_it_should_exclude_items(self):
        stream = Stream.range(10)
        odds = stream.exclude(lambda x: x % 2)
        self.assertListEqual(list(odds), [1, 3, 5, 7, 9])

    #   stream.exclude_nones()
    def test_it_should_exclude_values_of_None(self):
        items = ['foo', None, 'bar', None, 'baz', None]
        stream = Stream(items)
        not_none = stream.exclude_nones()
        self.assertListEqual(list(not_none),
                             [i for i in items if i is not None])

    #   stream.first
    def test_it_should_return_the_first_element_without_consuming_it(self):
        stream = Stream.range(10)
        self.assertEqual(stream.first, 0)
        self.assertEqual(stream.first, 0)
        self.assertEqual(stream.first, 0)
        self.assertListEqual(list(stream), list(xrange(10)))

    #   stream.filter()
    def test_it_should_filter_items(self):
        stream = Stream(range(10))
        stream = stream.filter(lambda item: item % 2)
        self.assertEqual(stream.sum(), 25)

        stream = Stream(dict((v, v) for v in xrange(100)))
        stream = stream.filter(lambda kv: kv[0] % 2)
        stream = stream.filter(lambda kv: kv[0] % 10, parallel=6)
        stream = stream.limit(5).keys()
        stream = list(stream)
        self.assertListEqual(list(stream), [1, 3, 5, 7, 9])

    #   stream.floats()
    def test_it_should_cast_a_stream_to_floats(self):
        items = list(xrange(10)) + ['0', '23', '99.999', 'foo', None]
        stream = Stream(items)
        floats = stream.floats()
        self.assertListEqual(list(floats), [float(i) for i in items[0:-2]])

    #   stream.instances_of()
    def test_it_should_filter_instances_of_a_class(self):
        items = list(xrange(10)) + ['foo', 'bar', 'baz']
        stream = Stream(items)
        strings = stream.instances_of(string_types)
        self.assertListEqual(list(strings), ['foo', 'bar', 'baz'])

        elements = list(xrange(100))
        # noinspection PyTypeChecker
        elements = elements + [str(item) for item in elements] + [None, None]
        strings = list(Stream(elements).instances_of(str))
        ints = list(Stream(elements).instances_of(int))
        self.assertEqual(len(strings), 100)
        self.assertTrue(all(isinstance(item, str) for item in strings))
        self.assertEqual(len(ints), 100)
        self.assertTrue(all(isinstance(item, int) for item in ints))

    #   stream.ints()
    def test_it_should_cast_a_stream_to_ints(self):
        items = list(xrange(10)) + ['0', '23', '99', 'foo', None]
        stream = Stream(items)
        ints = stream.ints()
        self.assertListEqual(list(ints), [int(i) for i in items[0:-2]])

    #   stream.key_map()
    def test_it_should_map_a_predicate_to_keys_in_key_value_pairs(self):
        items = range(10)
        stream = Stream(items).tuplify()
        mapped = stream.key_map(lambda k: k ** 2)
        self.assertListEqual(list(mapped), [(x ** 2, x) for x in xrange(10)])

    #   stream.keys()
    def test_it_should_return_only_keys(self):
        stream = Stream(list(zip(range(10), range(20, 30))) + ['foo'])
        keys = stream.keys()
        self.assertListEqual(list(keys), list(xrange(10)) + ['foo'])

    #   stream.largest()
    def test_it_should_filter_the_n_largest_items(self):
        stream = Stream(range(100))
        largest = stream.largest(10)
        self.assertListEqual(list(largest),
                             sorted(range(90, 100), reverse=True))

    #   stream.limit()
    def test_it_should_limit_the_size_of_the_stream(self):
        stream = Stream(xrange(10000000000))
        limited = stream.limit(10)
        self.assertListEqual(list(limited), list(xrange(10)))

        stream = Stream(xrange(100))
        stream = stream.limit(1000)
        self.assertListEqual(list(stream), list(xrange(100)))

    #   stream.longs()
    def test_it_should_cast_a_stream_to_longs(self):
        items = list(xrange(10)) + ['0', '23', '99', 'foo', None]
        stream = Stream(items)
        longs = stream.longs()
        self.assertListEqual(list(longs), [long(i) for i in items[0:-2]])

    #   stream.map()
    def test_it_should_map_a_function_to_the_stream(self):
        stream = Stream(range(10))
        stream = stream.map(lambda item: -item)
        self.assertEqual(max(stream), 0)

        stream = Stream(dict((v, v) for v in xrange(100)))
        stream = stream.values().skip(10).limit(3)
        self.assertListEqual(list(stream), [10, 11, 12])

    #   stream.median()
    def test_it_should_find_the_median(self):
        self.assertEqual(Stream(xrange(10)).median(), 5)
        self.assertEqual(Stream(xrange(11)).median(), 5)
        self.assertEqual(Stream(xrange(12)).median(), 6)

        arr = list(xrange(12))
        shuffle(arr)
        self.assertEqual(Stream(arr).median(), 6)

        arr = list(xrange(11))
        shuffle(arr)
        self.assertEqual(Stream(arr).median(), 5)

    def test_finding_the_median_of_an_empty_sequence_returns_None(self):
        self.assertIsNone(Stream(()).median())

    def test_finding_the_median_of_a_single_length_sequence_returns_it(self):
        self.assertEqual(Stream([1]).median(), 1)

    #   stream.nth()
    def test_nth(self):
        self.assertEqual(Stream(xrange(10)).nth(1), 0)
        self.assertEqual(Stream(xrange(10)).nth(2), 1)
        self.assertEqual(Stream(xrange(10)).nth(10), 9)
        self.assertIsNone(Stream(xrange(10)).nth(100))

    #   stream.odds()
    def test_it_should_filter_odds(self):
        stream = Stream(range(6))
        stream = stream.odds()
        self.assertListEqual(list(stream), [1, 3, 5])

        stream = Stream(xrange(200))
        stream = stream.odds()
        elements = list(stream)
        self.assertEqual(len(elements), 100)
        self.assertFalse(any(item % 2 == 0 for item in elements))

    #   stream.only_nones()
    def test_it_should_include_only_values_of_None(self):
        items = ['foo', None, 'bar', None, 'baz', None]
        stream = Stream(items)
        all_none = stream.only_nones()
        self.assertListEqual(list(all_none), [i for i in items if i is None])

    #   stream.only_trues()
    def test_it_should_include_only_truthy_values(self):
        items = ['', '', 0, None, 'foo', 'bar']
        stream = Stream(items)
        all_true = stream.only_trues()
        self.assertListEqual(list(all_true), [i for i in items if bool(i)])

    #   stream.only_falses()
    def test_it_should_include_only_falsey_values(self):
        items = ['', '', 0, None, 'foo', 'bar']
        stream = Stream(items)
        all_true = stream.only_falses()
        self.assertListEqual(list(all_true), [i for i in items if not bool(i)])

    #   stream.partly_distinct()
    def test_it_should_remove_most_repeated_items_from_a_long_stream(self):
        stream = Stream.concat(xrange(10001), xrange(10001)).partly_distinct()
        self.assertEqual(stream.count(), 10093)
        # The behavior of repoze.LRUCache doesn't seem to be fathomable, so we
        # can't test exactly which duplicates will be kept (without testing
        # LRUCache's cache ejection behavior).

    #   stream.peek()
    def test_it_should_apply_a_side_effect_to_the_stream(self):
        side_list = []
        stream = Stream.range(10)
        self.assertEqual(side_list, list(stream.peek(side_list.append)))

    #   Stream.range()
    def test_range(self):
        self.assertListEqual(list(Stream.range(100)), list(xrange(100)))

    #   stream.reduce()
    def test_it_should_reduce_the_stream(self):
        stream = Stream.range(10)
        reduced = stream.reduce(add)
        self.assertEqual(reduced, sum(range(10)))

    #   stream.regexp()
    def test_it_should_filter_by_regular_expression(self):
        stream = Stream((text_type(x) for x in xrange(100)))
        ones = stream.regexp(r'^1')
        self.assertListEqual(
            list(ones),
            ['1', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19'])

        stream = Stream(str(item) for item in xrange(1000))
        stream = stream.regexp(r"^10*$")
        stream = stream.ints()
        self.assertListEqual(list(stream), [1, 10, 100])

    #   stream.reversed()
    def test_it_should_reverse_the_stream(self):
        stream = Stream.range(10)
        reverse = stream.reversed()
        self.assertListEqual(list(reverse), list(reversed(range(10))))

    def test_reversed_should_reverse_the_stream(self):
        stream = Stream.range(10)
        reverse = reversed(stream)
        self.assertListEqual(list(reverse), list(reversed(range(10))))

    #   stream.skip()
    def test_it_should_skip_the_first_n_items(self):
        stream = Stream(range(20))
        skipped = stream.skip(10)
        self.assertListEqual(list(skipped), list(range(10, 20)))

    #   stream.smallest()
    def test_it_should_filter_the_n_smallest_items(self):
        stream = Stream(range(100))
        smallest = stream.smallest(10)
        self.assertListEqual(list(smallest), sorted(range(10)))

    #   stream.sorted()
    def test_it_should_sort_the_stream(self):
        stream = Stream(reversed(range(10)))
        sorted = stream.sorted()
        self.assertListEqual(list(sorted), list(xrange(10)))

    def test_it_should_reverse_sort_the_stream(self):
        stream = Stream.range(10)
        sorted = stream.sorted(reverse=True)
        self.assertListEqual(list(sorted), list(reversed(range(10))))

    def test_it_should_sort_the_stream_by_key(self):
        zipped = zip(reversed(list(xrange(10))), range(10))
        stream = Stream(reversed(list(zipped)))
        sorted = stream.sorted(key=itemgetter(1))
        self.assertListEqual(list(sorted),
                             list(zip(reversed(range(10)), range(10))))

    def test_it_should_reverse_sort_the_stream_by_key(self):
        stream = Stream(zip(reversed(range(10)), range(10)))
        sorted = stream.sorted(itemgetter(1), reverse=True)
        self.assertListEqual(
            list(sorted),
            list(reversed(list(zip(reversed(range(10)), range(10))))))

    #   stream.strings()
    def test_it_should_cast_a_stream_to_strings(self):
        items = range(10)
        stream = Stream(items)
        strings = stream.strings()
        self.assertListEqual(list(strings), [text_type(i) for i in items])

    #   stream.sum()
    def test_it_should_sum_a_stream(self):
        elements = list(xrange(5))
        int_result = Stream(elements).ints().sum()
        float_result = Stream(elements).floats().sum()
        decimal_result = Stream(elements).decimals().sum()
        self.assertEqual(int_result, 10)
        self.assertIsInstance(int_result, int)
        self.assertAlmostEqual(float_result, 10)
        self.assertIsInstance(float_result, float)
        self.assertEqual(decimal_result, Decimal("10"))
        self.assertIsInstance(decimal_result, Decimal)

    #   stream.tuplify()
    def test_it_should_expand_a_stream_to_tuples(self):
        tuples = Stream.range(10).tuplify()
        self.assertListEqual(list(tuples), [(i, i) for i in range(10)])

        tuples = Stream.range(10).tuplify(clones=4)
        self.assertListEqual(list(tuples), [(i, i, i, i) for i in range(10)])

    #   stream.value_map()
    def test_it_should_map_a_predicate_to_values_in_key_value_pairs(self):
        stream = Stream.range(10).tuplify()
        mapped = stream.value_map(lambda v: v ** 2)
        self.assertListEqual(list(mapped), [(x, x ** 2) for x in xrange(10)])

    #   stream.values()
    def test_it_should_include_only_values(self):
        stream = Stream(list(zip(range(10), range(100, 110),
                                 range(20, 30))) + ['foo'])
        values = stream.values()
        self.assertListEqual(list(values), list(range(20, 30)) + ['foo'])
