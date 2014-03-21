#!/usr/bin/env python
# -*- coding: utf-8 -*-


###############################################################################


from itertools import chain
from operator import mul
from unittest import TestCase, main

# noinspection PyUnresolvedReferences
from six.moves import xrange

from streams import Stream


###############################################################################


class StreamsCase(TestCase):

    def test_filter(self):
        stream = Stream(range(10))
        stream = stream.filter(lambda item: item % 2)
        self.assertEquals(stream.sum(), 25)

        stream = Stream({v: v for v in xrange(100)})
        stream = stream.filter(lambda (key, value): key % 2)
        stream = stream.filter(lambda (key, value): key % 10)
        stream = stream.limit(5).keys()
        self.assertItemsEqual(list(stream), [1, 3, 5, 7, 9])

    def test_map(self):
        stream = Stream(range(10))
        stream = stream.map(lambda item: -item)
        self.assertEquals(max(stream), 0)

        stream = Stream({v: v for v in xrange(100)})
        stream = stream.values().skip(10).limit(3)
        self.assertItemsEqual(list(stream), [10, 11, 12])

    def test_distinct(self):
        elements = chain(xrange(10), xrange(10), xrange(10), xrange(20))
        stream = Stream(elements)
        self.assertItemsEqual(list(stream.distinct()), list(xrange(20)))

    def test_sorted(self):
        elements = reversed(xrange(100))
        stream = Stream(elements)
        stream = stream.sorted()
        self.assertItemsEqual(list(stream), list(xrange(100)))

    def test_limit(self):
        stream = Stream(xrange(100))
        stream = stream.limit(50)
        self.assertEquals(stream.count(), 50)

        stream = Stream(xrange(100))
        stream = stream.limit(1000)
        self.assertEquals(stream.count(), 100)

    def test_skip(self):
        stream = Stream(xrange(100))
        stream = stream.skip(50)
        self.assertEquals(list(stream), list(xrange(50, 100)))

    def test_reversed(self):
        stream = Stream(xrange(100))
        stream = stream.reversed()
        self.assertEquals(list(stream), list(reversed(xrange(100))))

    def test_reduce(self):
        stream = Stream(xrange(11))
        stream = stream.skip(1)
        stream = stream.reduce(mul)
        self.assertEquals(stream, 3628800)

    def test_median(self):
        self.assertEquals(4, Stream(xrange(10)).median())
        self.assertEquals(4, Stream(xrange(11)).median())
        self.assertEquals(5, Stream(xrange(12)).median())

    def test_nth(self):
        self.assertEquals(0, Stream(xrange(10)).nth_element(1))
        self.assertEquals(1, Stream(xrange(10)).nth_element(2))
        self.assertEquals(9, Stream(xrange(10)).nth_element(10))
        self.assertIsNone(Stream(xrange(10)).nth_element(100))

    def test_any(self):
        self.assertTrue(Stream(xrange(10)).any())
        self.assertFalse(Stream([]).any())
        self.assertTrue(Stream(xrange(10)).any(lambda item: item > 5))
        self.assertTrue(Stream(xrange(10)).any(lambda item: item > 5, True))
        self.assertFalse(Stream(xrange(10)).any(lambda item: item < -1, False))

    def test_average(self):
        self.assertAlmostEqual(Stream(xrange(200)).average(), 99.5)

    def test_all(self):
        self.assertTrue(Stream(xrange(1, 10)).all())
        self.assertTrue(Stream(xrange(1, 10)).all(parallel=True))
        self.assertTrue(Stream([]).all(parallel=True))
        self.assertTrue(Stream([]).all())
        self.assertFalse(Stream(xrange(10)).all())
        self.assertFalse(Stream(xrange(10)).all(parallel=True))
        self.assertFalse(Stream(xrange(10)).all(lambda item: item < 5))
        self.assertTrue(Stream(xrange(10)).all(lambda item: item < 100))


if __name__ == "__main__":
    main()
