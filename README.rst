streams
=======

.. image:: https://travis-ci.org/9seconds/streams.svg?branch=master
   :target: https://travis-ci.org/9seconds/streams

.. image:: https://badge.fury.io/py/streams.png
    :target: https://badge.fury.io/py/streams.svg

This small library provides you with convenient streams deeply inspired by
Java 8 release. That release contains not only lambdas but pretty cool
Stream API which provides developers with possibilities to build sequental
and parallel aggregation on big collections or infinite data flows.

Frankly  I am not the Java guy but I have more or less the same workflow on
my previous projects where I actively used ``concurrent.futures`` or Gevent
pools to process pipelines of incoming data to reduce them to some scalar
value or aggregated data set. As a rule I used that approach to manage big or
unpredictable collections of similar data using some appropriate concurrency
where it is possible (threads on computations, coroutines on networking, etc.)

I saw how people are using the same pattern with ORMs but for generic cases
they still are trying to avoid mapping, filtering and reducing the results.
Actually this library tries to help.

Please checkout `official documentation <http://streams.readthedocs.org>`_
to get more information.