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

from ensure import ensure

# noinspection PyUnresolvedReferences
from six.moves import xrange

from streams import Stream


###############################################################################
class StreamTests(TestCase):
    ### Stream class methods
    def test_it_should_produce_a_range(self):
        s = Stream.range(10)
        ensure(s).is_a(Stream)
        ensure(list(s)).equals(range(10))

    def test_it_should_concatenate_iterables(self):
        s = Stream.concat(Stream.range(10), Stream.range(10))
        ensure(list(s)).equals(range(10) + range(10))

        stream = Stream.concat(xrange(10), xrange(10), xrange(10))
        ensure(list(stream.distinct())).equals(list(xrange(10)))

        stream = Stream.concat(xrange(10), xrange(10), xrange(10))
        ensure(stream.count()).equals(30)

    def test_it_should_iterate_on_a_seed_value(self):
        i = iter(Stream.iterate(lambda x: x * 10, 1))
        ensure(next(i)).equals(1)
        ensure(next(i)).equals(10)
        ensure(next(i)).equals(100)
        ensure(next(i)).equals(1000)

    ### Stream exhaustion tests
    def test_it_should_iterate_over_an_iterable(self):
        s = Stream.range(10)
        ensure(list(s)).equals(range(10))

    def test_it_should_iterate_over_an_iterable_multiple_times(self):
        s = Stream.range(10)
        ensure(list(s)).equals(range(10))
        ensure(list(s)).equals([])

    ### stream.all()
    def test_all(self):
        ensure(Stream(xrange(1, 10)).all(parallel=True)).is_true()
        ensure(Stream(xrange(1, 10)).all()).is_true()
        ensure(Stream([]).all()).is_true()
        ensure(Stream([]).all()).is_true()
        ensure(Stream(xrange(10)).all(parallel=True)).is_false()
        ensure(Stream(xrange(10)).all()).is_false()
        ensure(Stream(xrange(10)).all(lambda item: item < 5)).is_false()
        ensure(Stream(xrange(10)).all(lambda item: item < 100)).is_true()

    ### stream.any()
    def test_any(self):
        ensure(Stream(xrange(10)).any()).is_true()
        ensure(Stream([]).any()).is_false()
        ensure(Stream(xrange(10)).any(lambda item: item > 5,
                                      parallel=True)).is_true()
        ensure(Stream(xrange(10)).any(lambda item: item > 5)).is_true()
        ensure(Stream(xrange(10)).any(lambda item: item < -1,
                                      parallel=True)).is_false()

    ### stream.average()
    def test_average(self):
        self.assertAlmostEqual(Stream(xrange(200)).average(), 99.5)

    ### stream.chain()
    def test_it_should_chain_iterables_together(self):
        s = Stream((range(10), range(10)))
        ensure(list(s.chain())).equals(range(10) + range(10))

    ### stream.count()
    def test_it_should_count_the_number_of_items_in_the_stream(self):
        s = Stream.range(100)
        ensure(s.count()).equals(100)

    def test_it_should_count_the_number_of_occurrences_in_the_stream(self):
        s = Stream('foobar')
        ensure(s.count('o')).equals(2)
        s = Stream('foobar')
        ensure(s.count('b')).equals(1)

    ### stream.divisible by()
    def test_it_should_filter_by_divisibility(self):
        s = Stream(range(6))
        s = s.divisible_by(2)
        ensure(list(s)).equals([0, 2, 4])

        stream = Stream(xrange(2000))
        stream = stream.ints().divisible_by(10)
        self.assertEqual(stream.count(), 200)

        stream = Stream(xrange(2000))
        stream = stream.divisible_by(1000)
        self.assertEquals(list(stream), [0, 1000])

    ### stream.decimals()
    def test_it_should_cast_a_stream_to_decimals(self):
        from decimal import Decimal
        items = range(10) + ['0', '23', '99', 'foo', None]
        s = Stream(items)
        decimals = s.decimals()
        ensure(list(decimals)).equals([Decimal(i) for i in items[0:-2]])

    ### stream.distinct()
    def test_it_should_remove_repeated_items_from_the_stream(self):
        elements = chain(xrange(10), xrange(10), xrange(10), xrange(20))
        stream = Stream(elements)
        ensure(list(stream.distinct())).equals(list(xrange(20)))

    ### stream.evens()
    def test_it_should_filter_evens(self):
        s = Stream(range(6))
        s = s.evens()
        ensure(list(s)).equals([0, 2, 4])

        stream = Stream(xrange(200))
        stream = stream.ints().evens()
        elements = list(stream)
        ensure(len(elements)).equals(100)
        ensure(all(item % 2 == 0 for item in elements)).is_true()

    ### stream.exclude()
    def test_it_should_exclude_items(self):
        s = Stream.range(10)
        odds = s.exclude(lambda x: x % 2)
        ensure(list(odds)).equals([1, 3, 5, 7, 9])

    ### stream.exclude_nones()
    def test_it_should_exclude_values_of_None(self):
        items = ['foo', None, 'bar', None, 'baz', None]
        s = Stream(items)
        not_none = s.exclude_nones()
        ensure(list(not_none)).equals([i for i in items if i is not None])

    ### stream.first
    def test_it_should_return_the_first_element_of_a_stream_without_consuming_the_stream(self):
        s = Stream.range(10)
        ensure(s.first).equals(0)
        ensure(s.first).equals(0)
        ensure(s.first).equals(0)
        ensure(list(s)).equals(range(10))

    ### stream.filter()
    def test_it_should_filter_items(self):
        stream = Stream(range(10))
        stream = stream.filter(lambda item: item % 2)
        ensure(stream.sum()).equals(25)

        stream = Stream(dict((v, v) for v in xrange(100)))
        stream = stream.filter(lambda kv: kv[0] % 2)
        stream = stream.filter(lambda kv: kv[0] % 10, parallel=6)
        stream = stream.limit(5).keys()
        stream = list(stream)
        ensure(list(stream)).equals([1, 3, 5, 7, 9])

    ### stream.floats()
    def test_it_should_cast_a_stream_to_floats(self):
        items = range(10) + ['0', '23', '99.999', 'foo', None]
        s = Stream(items)
        floats = s.floats()
        ensure(list(floats)).equals([float(i) for i in items[0:-2]])

    ### stream.instances_of()
    def test_it_should_filter_instances_of_a_class(self):
        items = range(10) + ['foo', 'bar', 'baz']
        s = Stream(items)
        strings = s.instances_of(basestring)
        ensure(list(strings)).equals(['foo', 'bar', 'baz'])

        elements = list(xrange(100))
        # noinspection PyTypeChecker
        elements = elements + [str(item) for item in elements] + [None, None]
        strings = list(Stream(elements).instances_of(str))
        ints = list(Stream(elements).instances_of(int))
        ensure(len(strings)).equals(100)
        ensure(all(isinstance(item, str) for item in strings)).is_true()
        ensure(len(ints)).equals(100)
        ensure(all(isinstance(item, int) for item in ints)).is_true()

    ### stream.ints()
    def test_it_should_cast_a_stream_to_ints(self):
        items = range(10) + ['0', '23', '99', 'foo', None]
        s = Stream(items)
        ints = s.ints()
        ensure(list(ints)).equals([int(i) for i in items[0:-2]])

    ### stream.key_map()
    def test_it_should_map_a_predicate_to_keys_in_key_value_pairs(self):
        items = range(10)
        s = Stream(items).tuplify()
        mapped = s.key_map(lambda k: k ** 2)
        ensure(list(mapped)).equals([(x ** 2, x) for x in xrange(10)])

    ### stream.keys()
    def test_it_should_return_only_keys(self):
        s = Stream(zip(range(10), range(20, 30)) + ['foo'])
        keys = s.keys()
        ensure(list(keys)).equals(range(10) + ['foo'])

    ### stream.largest()
    def test_it_should_filter_the_n_largest_items(self):
        s = Stream(range(100))
        largest = s.largest(10)
        ensure(list(largest)).equals(sorted(range(90, 100), reverse=True))

    ### stream.limit()
    def test_it_should_limit_the_size_of_the_stream(self):
        s = Stream(xrange(10000000000))
        limited = s.limit(10)
        ensure(list(limited)).equals(range(10))

        stream = Stream(xrange(100))
        stream = stream.limit(1000)
        ensure(list(stream)).equals(list(xrange(100)))

    ### stream.longs()
    def test_it_should_cast_a_stream_to_longs(self):
        items = range(10) + ['0', '23', '99', 'foo', None]
        s = Stream(items)
        longs = s.longs()
        ensure(list(longs)).equals([long(i) for i in items[0:-2]])

    ### stream.map()
    def test_it_should_map_a_function_to_the_stream(self):
        stream = Stream(range(10))
        stream = stream.map(lambda item: -item)
        ensure(max(stream)).equals(0)

        stream = Stream(dict((v, v) for v in xrange(100)))
        stream = stream.values().skip(10).limit(3)
        ensure(list(stream)).equals([10, 11, 12])

    ### stream.median()
    def test_it_should_find_the_median(self):
        ensure(Stream(xrange(10)).median()).equals(5)
        ensure(Stream(xrange(11)).median()).equals(5)
        ensure(Stream(xrange(12)).median()).equals(6)

        arr = list(xrange(12))
        shuffle(arr)
        ensure(Stream(arr).median()).equals(6)

        arr = list(xrange(11))
        shuffle(arr)
        ensure(Stream(arr).median()).equals(5)

    def test_it_should_return_None_if_finding_the_median_of_an_empty_sequence(self):
        ensure(Stream(()).median()).is_none()

    def test_it_should_return_the_first_element_if_finding_the_median_of_a_single_length_sequence(self):
        ensure(Stream([1]).median()).equals(1)

    ### stream.nth()
    def test_nth(self):
        ensure(Stream(xrange(10)).nth(1)).equals(0)
        ensure(Stream(xrange(10)).nth(2)).equals(1)
        ensure(Stream(xrange(10)).nth(10)).equals(9)
        ensure(Stream(xrange(10)).nth(100)).is_none()

    ### stream.odds()
    def test_it_should_filter_odds(self):
        s = Stream(range(6))
        s = s.odds()
        ensure(list(s)).equals([1, 3, 5])

        stream = Stream(xrange(200))
        stream = stream.odds()
        elements = list(stream)
        ensure(len(elements)).equals(100)
        ensure(any(item % 2 == 0 for item in elements)).is_false()

    ### stream.only_nones()
    def test_it_should_include_only_values_of_None(self):
        items = ['foo', None, 'bar', None, 'baz', None]
        s = Stream(items)
        all_none = s.only_nones()
        ensure(list(all_none)).equals([i for i in items if i is None])

    ### stream.only_trues()
    def test_it_should_include_only_truthy_values(self):
        items = ['', '', 0, None, 'foo', 'bar']
        s = Stream(items)
        all_true = s.only_trues()
        ensure(list(all_true)).equals([i for i in items if bool(i)])

    ### stream.only_falses()
    def test_it_should_include_only_falsey_values(self):
        items = ['', '', 0, None, 'foo', 'bar']
        s = Stream(items)
        all_true = s.only_falses()
        ensure(list(all_true)).equals([i for i in items if not bool(i)])

    ### stream.peek()
    def test_it_should_apply_a_side_effect_to_the_stream(self):
        side_list = []
        s = Stream.range(10)
        ensure(side_list).equals(list(s.peek(side_list.append)))

    ### Stream.range()
    def test_range(self):
        ensure(list(Stream.range(100))).equals(list(xrange(100)))

    ### stream.reduce()
    def test_it_should_reduce_the_stream(self):
        s = Stream.range(10)
        reduced = s.reduce(add)
        ensure(reduced).equals(sum(range(10)))

    ### stream.regexp()
    def test_it_should_filter_by_regular_expression(self):
        s = Stream((unicode(x) for x in xrange(100)))
        ones = s.regexp(r'^1')
        ensure(list(ones)).equals(['1', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19'])

        stream = Stream(str(item) for item in xrange(1000))
        stream = stream.regexp(r"^10*$")
        stream = stream.ints()
        self.assertListEqual(list(stream), [1, 10, 100])

    ### stream.reversed()
    def test_it_should_reverse_the_stream(self):
        s = Stream.range(10)
        reverse = s.reversed()
        ensure(list(reverse)).equals(list(reversed(range(10))))

    def test_reversed_should_reverse_the_stream(self):
        s = Stream.range(10)
        reverse = reversed(s)
        ensure(list(reverse)).equals(list(reversed(range(10))))

    ### stream.skip()
    def test_it_should_skip_the_first_n_items(self):
        s = Stream(range(20))
        skipped = s.skip(10)
        ensure(list(skipped)).equals(range(10, 20))

    ### stream.smallest()
    def test_it_should_filter_the_n_smallest_items(self):
        s = Stream(range(100))
        smallest = s.smallest(10)
        ensure(list(smallest)).equals(sorted(range(10)))

    ### stream.sorted()
    def test_it_should_sort_the_stream(self):
        s = Stream(reversed(range(10)))
        sorted = s.sorted()
        ensure(list(sorted)).equals(range(10))

    def test_it_should_reverse_sort_the_stream(self):
        s = Stream.range(10)
        sorted = s.sorted(reverse=True)
        ensure(list(sorted)).equals(list(reversed(range(10))))

    def test_it_should_sort_the_stream_by_key(self):
        s = Stream(reversed(zip(reversed(range(10)), range(10))))
        sorted = s.sorted(key=itemgetter(1))
        ensure(list(sorted)).equals(list(zip(reversed(range(10)), range(10))))

    def test_it_should_reverse_sort_the_stream_by_key(self):
        s = Stream(zip(reversed(range(10)), range(10)))
        sorted = s.sorted(itemgetter(1), reverse=True)
        ensure(list(sorted)).equals(list(reversed(zip(reversed(range(10)), range(10)))))

    ### stream.strings()
    def test_it_should_cast_a_stream_to_strings(self):
        items = range(10)
        s = Stream(items)
        strings = s.strings()
        ensure(list(strings)).equals([unicode(i) for i in items])

    ### stream.sum()
    def test_it_should_sum_a_stream(self):
        elements = list(xrange(5))
        int_result = Stream(elements).ints().sum()
        float_result = Stream(elements).floats().sum()
        decimal_result = Stream(elements).decimals().sum()
        ensure(int_result).equals(10)
        ensure(int_result).is_an(int)
        self.assertAlmostEqual(float_result, 10)
        ensure(float_result).is_a(float)
        ensure(decimal_result).equals(Decimal("10"))
        ensure(decimal_result).is_a(Decimal)

    ### stream.tuplify()
    def test_it_should_expand_a_stream_to_tuples(self):
        tuples = Stream.range(10).tuplify()
        ensure(list(tuples)).equals([(i, i) for i in range(10)])

        tuples = Stream.range(10).tuplify(clones=4)
        ensure(list(tuples)).equals([(i, i, i, i) for i in range(10)])

    ### stream.value_map()
    def test_it_should_map_a_predicate_to_values_in_key_value_pairs(self):
        s = Stream.range(10).tuplify()
        mapped = s.value_map(lambda v: v ** 2)
        ensure(list(mapped)).equals([(x, x ** 2) for x in xrange(10)])

    ### stream.values()
    def test_it_should_include_only_values(self):
        s = Stream(zip(range(10), range(100, 110), range(20, 30)) + ['foo'])
        values = s.values()
        ensure(list(values)).equals(range(20, 30) + ['foo'])
