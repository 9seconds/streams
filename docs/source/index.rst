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
Python.


What is Stream?
---------------

I supposed you've worked with Django and you've been using its ORM a lot. I
will try to lead you to the idea of functional streams by example. Actually
I did no Django for a while and syntax might be outdated a bit or I may
confuse you so you are free to correct me through issue or pull request.
Please do it, I appreciate your feedback.

If you didn't work with any ORM just try to follow the idea,
I will try to explain what is going on and things that really matter.

Let's go back to default Django example: libraries and books. Let's assume
that we have app up and running and it does some data management from your
beloved database. Let's say you want to fetch some recent books.

    .. code-block:: python

        from library.models import Book

        books = Book.objects.filter(pub_date__year=2014)

Good, isn't it? You have a collection of models called ``Book`` which possibly
presents books in your app. And you want to have only those which were
published in 2014. Good, figured out. Let's go further. Let's say you want
to be more specific and you want to have only bestsellers. It is ok.

    .. code-block:: python

        from library.models import Book

        books = Book.objects.filter(pub_date__year=2014)
        bestsellers = books.order_by("-sales_count")[:10]

You can do it like this. But why is it better than this approach?

    .. code-block:: python

        from operator import attrgetter
        from library.models import Book

        books = Book.objects.all()
        books = [book for book in books if book.pub_date.year == 2014]
        bestsellers = sorted(books, key=attrgetter("sales_count"), reverse=True)
        bestsellers = bestsellers[:10]

You will get the same result, right?

Contents:

.. toctree::
   :maxdepth: 2

   user-guide
   api


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

