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

You will get the same result, right?