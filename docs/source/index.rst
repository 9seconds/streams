.. Streams documentation master file, created by
   sphinx-quickstart on Sun Mar 30 11:18:49 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Streams's documentation!
===================================

Streams is an easy to use library to allow you to interpret your information
as a data flow and process it in this way. It allows you parallel processing
of a data flow and you can control it.

Actually Streams is dramatically inspired by Java 8 Stream API. Of course it
is not a new beast in the zoo, I used the same approach in several projects
before but this pattern goes to mainstream now and it is good to have it in
Python too.

Just several examples to help you to feel what is it:

    .. code-block:: python

        from requests import get
        from operator import itemgetter

        average_price = Stream(urls)                             \ # make a stream from the list of urls
            .map(requests.get, parallel=4)                       \ # do url  fetching in parallel. 4 threads / greenlets
            .map(lambda response: response.json()["model"])     \ # extract required field from JSON.
            .exclude(lambda model: model["deleted_at"] is None) \ # we need only active accounts so filter out deleted ones
            .map(itemgetter("price"))                            \ # get a price from the model
            .decimals()                                          \ # convert prices into decimals
            .average()                                           \ # calulate average from the list

And not let's check the piece of code which does almost the same.

    .. code-block:: python

        from concurrent.futures import ThreadPoolExecutor
        from requests import get

        with ThreadPoolExecutor(4) as pool:
            average_price = Decimal("0.00")
            fetched_items = pool.map(requests.get, urls)
            for response in fetched_items:
                model = response.json()["model]
                if model["deleted_at"] is None: continue
                sum_of += Decimal(model["price"])
            average_price /= len(urls)

So this is Stream approach. Streams are lazy library and won't do anything
if it is not needed. Let's say you have urls as iterator and it contains
several billions of URLs you can't fit into the memory (ThreadPoolExecutor
creates a list in the memory) or you want to build a pipeline of your data
management and manipulate it according to some conditions, checkout Streams,
maybe it will help you to create more accurate and maintainable code.

Just suppose Streams as a pipes from your \*nix environment but migrated into
Python. It also has some cool features you need to know about:

    * Laziness,
    * Small memory footprint even for massive data sets,
    * Automatic and configurable parallelization,
    * Smart concurrent pool management.

Checkout Design decisions to understand how it works. It has no magic at all.

Contents:

.. toctree::
   :maxdepth: 2

   user-guide
   design-decisions


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

