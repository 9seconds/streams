User Guide
==========

I supposed you've worked with Django and you've been using its ORM a lot. I
will try to lead you to the idea of functional streams by example. Actually
I did no Django for a while and syntax might be outdated a bit or I may
confuse you so you are free to correct me through issue or pull request.
Please do it, I appreciate your feedback.

If you didn't work with any ORM just try to follow the idea,
I will try to explain what is going on and things that really matter.


What is Stream?
---------------

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

You will get the same result, right? Actually no. Look, on filtering step you
fetch all objects from the database and process them all. It is ok if you
have a dozen of models in your database but it can be big bottleneck if your
data is growing. That's why everyone is trying to move as much filtering as
possible into the database. Database knows how to manage your data
accurately and what do to in the most efficient way. It will use indexes etc
to speedup whole process and you do not need to do full scan everytime. It is
best practice to fetch only that data you actually need from the database.

So instead of

    .. code-block:: sql

        SELECT * FROM book

you do

    .. code-block:: sql

        SELECT * FROM book
            WHERE EXTRACT(year FROM "pub_date") == 2014
            ORDER BY sales_count DESC
            LIMIT 10

Sounds legit. But let's checkout how it looks like when do you work with ORM.
Let's go back to our example:

    .. code-block:: python

        books = Book.objects.filter(pub_date__year=2014)
        bestsellers = books.order_by("-sales_count")[:10]

or in a short way

    .. code-block:: python

        bestsellers = Book.objects \
            .filter(pub_date__year=2014) \
            .order_by("-sales_count")[:10]

You may assume it like a data stream you are processing on every step. First
you set initial source of data, this is ``Book.objects.all()``. Good. You may
consider it as an iterable flow of data and you apply processing functions on
that stream, first if filtering, second is sorting, third is slicing. You
process the flow, not every objects, this is crucial concept. Everytime after
execution of some flow (or ``QuerySet``) method you get another instance of
the same flow but with your modifications.

You may suppose that Streams library to provide you the same functionality but
for any iterable. Of course this is not that efficient as Django ORM which
knows the context of database and helps you to execute your queries in the
most efficient way.


How to use Streams
------------------

Now you got an idea of Streams: to manage data flow itself, not every
component. You can build your own toy map/reduce stuff with it if you really
need to have it. Our you can just filter and process your data to exclude some
Nones etc in parallel or to have some generic way to do it. It is up to you,
I'll just show you some examples and if you want to have more information
just go to the API documentation

So, for simplicity let's assume that you have giant gzipped CSV,
in 10 GB. And you can use only 1GB of your memory so it is not possible to
put everything in memory at once. This CSV has 5 columns, ``author_id``,
``book_name``.

Yeah, books again. Why not?

So your boss asked you to implement function which will read this csvfile and
do some optional filtering on it. Also you must fetch the data from predefined
external sources, search on prices in different shops (Amazon at least) and
write some big XML file with an average price.

I some explanation on the go.

    .. code-block:: python

        from csv import reader
        from gzip import open as gzopen
        from collections import namedtuple
        try:
            from xml.etree import cElementTree as ET
        except ImportError:
            from xml.etree import ElementTree as ET
        from streams import Stream
        from other_module import shop_prices_fetch, author_fetch, publisher_fetch


        def extract_averages(csv_filename, xml_filename,
                             author_prefix=None, count=None, publisher=None, shops=None,
                             available=None):
            file_handler = gzopen(csv_filename, "r")
            try:
                csv_iterator = reader(file_handler)

                # great, we have CSV iterator right now which will read our
                # file line by line now let's convert it to stream
                stream = Stream(csv_iterator)

                # now let's fetch author names. Since every row looks like a
                # tuple of (key, value) where key is an author_id and value is
                # a book name we can do key_mapping here. And let's do it in
                # parallel it is I/O bound
                stream = stream.key_map(author_fetch, parallel=True)

                # okay, now let's keep only author name here
                stream = stream.map(lambda (author, book): (author["name"], book))

                # we have author prefix, right?
                if author_prefix is not None:
                    stream = stream.filter(lambda (author, book): author.startswith(author_prefix))

                # let's fetch publisher now. Let's do it in 10 threads
                if publisher is not None:
                    stream = stream.map(
                        lambda (author, book): (author, book, publisher_fetch(author, book)),
                        parallel=10
                    )
                    stream = stream.filter(lambda item: item[-1] == publisher)
                    # we do not have to have publisher now, let's remove it
                    stream = stream.map(lambda item: item[:2])

                # good. Let's compose the list of shops here
                stream.map(
                    lambda (author, book): (author, book, shop_prices_fetch(author, book, shops))
                )

                # now let's make averages
                stream.map(lambda item: item[:2] + sum(item[3]) / len(item[3]))

                # let's remove unavailable books now.
                if available is not None:
                    if available:
                        stream = stream.filter(lambda item: item[-1])
                    else:
                        stream = stream.filter(lambda item: not item[-1])

                # ok, great. Now we have only those entries which we are requiring
                # let's compose xml now. Remember whole our data won't fit in memory.
                with open(xml_filename, "w") as xml:
                    xml.write("<?xml version='1.0' encoding='UTF-8' standalone='yes'?>\n")
                    xml.write("<books>\n")
                    for author, book, average in stream:
                        book_element = ET.Element("book")
                        ET.SubElement(book_element, "name").text = unicode(book)
                        ET.SubElement(book_element, "author").text = unicode(author)
                        ET.SubElement(book_element, "average_price").text = unicode(average)
                        xml.write(ET.dumps(book_element) + "\n")
                    xml.write("</books>\n")
            finally:
                file_handler.close()

That's it. On every step we've manipulated with given stream to direct it in
the way we need. We've parallelized where neccessary and actually nothing was
executed before we started to iterate the stream. Stream is lazy and it yields
one record by one so we haven't swaped.

I guess it is a time to proceed to API documentation. Actually you need to
check only Stream class methods documentation, the rest of are utility ones.