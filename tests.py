#!/usr/bin/env python
# -*- coding: utf-8 -*-


###############################################################################


from itertools import chain
from operator import mul
from random import shuffle
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
        stream = stream.filter(lambda kv: kv[0] % 10)
        stream = stream.limit(5).keys()
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


if __name__ == "__main__":
    main()
