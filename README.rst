streams
=======

.. image:: https://travis-ci.org/9seconds/streams.svg?branch=master
   :target: https://travis-ci.org/9seconds/streams

*Real documentation is still ungoing. This is just a short description.*

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

Checkout `how it looks with Java <http://download.java.net/jdk8/docs/api/java/util/stream/Stream.html>`_.

.. code-block:: java

     int sum = widgets.stream()
                      .filter(w -> w.getColor() == RED)
                      .mapToInt(w -> w.getWeight())
                      .sum();

Nice. Now it goes Streams one

.. code-block:: python

     sum = Stream(widgets) \
         .filter(lambda widget: widget.get_color() == RED) \
         .map(lambda widget: widget.get_weight()) \
         .ints() \
         .sum()

Looks similar and actually it works like this. Please be notices that Streams
is trying to parallelize almost everything and by default maps and filters
are parallel. But if you don't like it you could disable it or mix your own
parallel executors in appropriate places. Check this out

.. code-block:: python

     money_median = Stream(urls) \
         .map(requests.get, GeventExecutor) \            # fetch APIs
         .map(lambda response: response.json(), None) \  # not parallel
         .chain() \  # suppose we have arrays as JSONs, flat iteration
         .ints()  \  # throw away garbage, keep only ints here
         .map(fetch_object_by_id_from_db, ThreadPoolExecutor)  # guess what
         .exclude_nones()                    # but we do not need None here, just real objects
         .map(lambda model: model["money"])  # get the money from each model
         .median()                           # let's get the median of money then

Yes, the real example. And do not forget we have it pipelines so everything
is trying to go in parallel. Streams are trying to use as much iterators as
possible, it is lazy and won't do anything unless you ask about it (like
terminal operation such as ``median()``)
