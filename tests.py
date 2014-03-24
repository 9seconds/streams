#!/usr/bin/env python
# -*- coding: utf-8 -*-


###############################################################################


from itertools import chain
from operator import mul
from random import shuffle

try:
    from cdecimal import Decimal
except ImportError:
    from decimal import Decimal
try:
    from unittest2 import TestCase, main
except ImportError:
    from unittest import TestCase, main

# noinspection PyUnresolvedReferences
from six.moves import xrange

from streams import Stream


###############################################################################


class StreamsCase(TestCase):

    def test_filter(self):
        stream = Stream(range(10))
        stream = stream.filter(lambda item: item % 2)
        self.assertEqual(stream.sum(), 25)

        stream = Stream(dict((v, v) for v in xrange(100)))
        stream = stream.filter(lambda kv: kv[0] % 2)
        stream = stream.filter(lambda kv: kv[0] % 10, parallel=True)
        stream = stream.limit(5).keys()
        stream = list(stream)
        self.assertListEqual(list(stream), [1, 3, 5, 7, 9])

    def test_map(self):
        stream = Stream(range(10))
        stream = stream.map(lambda item: -item)
        self.assertEqual(max(stream), 0)

        stream = Stream(dict((v, v) for v in xrange(100)))
        stream = stream.values().skip(10).limit(3)
        self.assertListEqual(list(stream), [10, 11, 12])

    def test_distinct(self):
        elements = chain(xrange(10), xrange(10), xrange(10), xrange(20))
        stream = Stream(elements)
        self.assertListEqual(list(stream.distinct()), list(xrange(20)))

    def test_sorted(self):
        elements = reversed(xrange(100))
        stream = Stream(elements)
        stream = stream.sorted()
        self.assertListEqual(list(stream), list(xrange(100)))

    def test_limit(self):
        stream = Stream(xrange(100))
        stream = stream.limit(50)
        self.assertEqual(stream.count(), 50)

        stream = Stream(xrange(100))
        stream = stream.limit(1000)
        self.assertEqual(stream.count(), 100)

    def test_skip(self):
        stream = Stream(xrange(100))
        stream = stream.skip(50)
        self.assertEqual(list(stream), list(xrange(50, 100)))

    def test_reversed(self):
        stream = Stream(xrange(100))
        stream = stream.reversed()
        self.assertEqual(list(stream), list(reversed(xrange(100))))

    def test_reduce(self):
        stream = Stream(xrange(11))
        stream = stream.skip(1)
        stream = stream.reduce(mul)
        self.assertEqual(stream, 3628800)

    def test_median(self):
        self.assertEqual(5, Stream(xrange(10)).median())
        self.assertEqual(5, Stream(xrange(11)).median())
        self.assertEqual(6, Stream(xrange(12)).median())

        arr = list(xrange(12))
        shuffle(arr)
        self.assertEqual(6, Stream(arr).median())

        arr = list(xrange(11))
        shuffle(arr)
        self.assertEqual(5, Stream(arr).median())

    def test_nth(self):
        self.assertEqual(0, Stream(xrange(10)).nth_element(1))
        self.assertEqual(1, Stream(xrange(10)).nth_element(2))
        self.assertEqual(9, Stream(xrange(10)).nth_element(10))
        self.assertIsNone(Stream(xrange(10)).nth_element(100))

    def test_any(self):
        self.assertTrue(Stream(xrange(10)).any())
        self.assertFalse(Stream([]).any())
        self.assertTrue(Stream(xrange(10)).any(lambda item: item > 5,
                                               parallel=None))
        self.assertTrue(Stream(xrange(10)).any(lambda item: item > 5))
        self.assertFalse(Stream(xrange(10)).any(lambda item: item < -1,
                                                parallel=None))

    def test_average(self):
        self.assertAlmostEqual(Stream(xrange(200)).average(), 99.5)

    def test_all(self):
        self.assertTrue(Stream(xrange(1, 10)).all(parallel=None))
        self.assertTrue(Stream(xrange(1, 10)).all())
        self.assertTrue(Stream([]).all())
        self.assertTrue(Stream([]).all())
        self.assertFalse(Stream(xrange(10)).all(parallel=None))
        self.assertFalse(Stream(xrange(10)).all())
        self.assertFalse(Stream(xrange(10)).all(lambda item: item < 5))
        self.assertTrue(Stream(xrange(10)).all(lambda item: item < 100))

    def test_range(self):
        self.assertListEqual(list(Stream.range(100)), list(xrange(100)))

    def test_concat(self):
        stream = Stream.concat(xrange(10), xrange(10), xrange(10))
        self.assertListEqual(list(stream.distinct()), list(xrange(10)))

        stream = Stream.concat(xrange(10), xrange(10), xrange(10))
        self.assertEqual(stream.count(), 30)

    def test_first(self):
        stream = Stream(xrange(10))
        self.assertEqual(stream.first, 0)
        self.assertEqual(stream.first, 0)
        self.assertEqual(stream.first, 0)
        self.assertEqual(stream.count(), 10)

    def test_regexp(self):
        stream = Stream(str(item) for item in xrange(1000))
        stream = stream.regexp(r"^10*$")
        stream = stream.ints()
        self.assertListEqual(list(stream), [1, 10, 100])

    def test_divisibleby(self):
        stream = Stream(xrange(2000))
        stream = stream.ints().divisible_by(10)
        self.assertEqual(stream.count(), 200)

        stream = Stream(xrange(2000))
        stream = stream.divisible_by(1000)
        self.assertEquals(list(stream), [0, 1000])

    def test_evens(self):
        stream = Stream(xrange(200))
        stream = stream.ints().evens()
        elements = list(stream)
        self.assertEqual(len(elements), 100)
        self.assertTrue(all(item % 2 == 0 for item in elements))

    def test_odds(self):
        stream = Stream(xrange(200))
        stream = stream.odds()
        elements = list(stream)
        self.assertEqual(len(elements), 100)
        self.assertFalse(any(item % 2 == 0 for item in elements))

    def test_instances_of(self):
        elements = list(xrange(100))
        # noinspection PyTypeChecker
        elements = elements + [str(item) for item in elements] + [None, None]
        strings = list(Stream(elements).instances_of(str))
        ints = list(Stream(elements).instances_of(int))
        self.assertEqual(len(strings), 100)
        self.assertTrue(all(isinstance(item, str) for item in strings))
        self.assertEqual(len(ints), 100)
        self.assertTrue(all(isinstance(item, int) for item in ints))

    def test_exclude_nones(self):
        elements = list(xrange(100)) + [None, None]
        without_nones = list(Stream(elements).exclude_nones())
        self.assertEqual(without_nones, list(xrange(100)))

    def test_exclude(self):
        elements = list(xrange(100))
        evens = list(Stream(elements).exclude(lambda item: item % 2 != 0))
        evens2 = list(Stream(elements).evens())
        self.assertEqual(evens, evens2)

    def test_only_trues(self):
        elements = list(xrange(5)) + [True, False, True, None, 1, object()]
        stream = Stream(elements).only_trues()
        self.assertTrue(all(bool(item) for item in stream))

    def test_only_falses(self):
        elements = list(xrange(5)) + [True, False, True, None, 1, object()]
        stream = Stream(elements).only_falses()
        self.assertFalse(any(bool(item) for item in stream))

    def test_only_nones(self):
        elements = list(xrange(5)) + [True, False, True, None, 1, object()]
        stream = Stream(elements).only_nones()
        self.assertTrue(all(item is None for item in stream))

    def test_count(self):
        elements = list(xrange(5)) * 2
        self.assertEqual(Stream(elements).count(), 10)
        self.assertEqual(Stream(elements).count(1), 2)

    def test_sum(self):
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


if __name__ == "__main__":
    main()
