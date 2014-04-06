# -*- coding: utf-8 -*-


###############################################################################


from collections import defaultdict
from functools import partial
from multiprocessing import cpu_count
from threading import RLock

from six import iteritems, iterkeys, itervalues

from .executors import ParallelExecutor, ProcessPoolExecutor
from .executors.mixins import PoolOfPoolsMixin


###############################################################################


class ExecutorPool(object):
    """
    Executor pool for :py:class:`PoolOfPools` which does accurate and
    intelligent management for the pools of predefined classes.

    Basically it tries to reuse existing executors if possible. If it is not
    possible it creates new ones.

    Just an example: you've done a big mapping of the data in 10 threads. As a
    rule you need to shutdown and clean this pool. But a bit later you see that
    you need for the pool of 4 threads. Why not to reuse existing pool? This
    class allow you to do that and it tracks that 6 threads are idle. So if
    you will have a task where you need <= 6 threads it will reuse that pool
    also. Task with 4 threads may continue to work in parallel but you have
    6 threads you can occupy. So this is the main idea.

    Also it tries to squash pools into single instance if you have several
    which idle by expanding an amount of workers in one instance throwing out
    another one.
    """

    def __init__(self, worker_class):
        """
        Constructor of the class. worker_class has to be a class which
        supports required interface and behaviour, it has to be an instance
        of :py:class:`streams.executors.mixins.PoolOfPoolsMixin`.

        :param PoolOfPoolsMixin worker_class: The class of executors this pool
                                              has to maintain.
        """
        assert issubclass(worker_class, PoolOfPoolsMixin)

        self.worker_class = worker_class
        self.workers = defaultdict(lambda: [])
        self.lock = RLock()

    def get_any(self):
        """
        Returns any map function, it is undetermined how many workers does it
        have. As a rule, you get a minimal amount of workers within a pool of
        executors.
        """
        with self.lock:
            return self.get(min(iterkeys(self.workers)))

    def get(self, required_workers):
        """
        Returns a mapper which guarantees that you can utilize given number of
        workers.

        :param int required_workers: The number of workers you need to utilize
                                     for your task.
        """
        assert required_workers > 0

        with self.lock:
            self.squash()
            worker, availability = self.get_suitable_worker(required_workers)
            if worker is None:
                worker = self.worker_class(required_workers)
                availability = required_workers
            availability -= required_workers
            if availability > 0:
                self.workers[availability].append(worker)

        return partial(worker.map,
                       required_workers=required_workers,
                       callback=self.worker_finished)

    def squash(self):
        """
        Squashes pools and tries to minimize the amount of pools available to
        avoid unnecessary fragmentation and complexity.
        """
        if not self.workers:
            return
        with self.lock:
            for avail in list(iterkeys(self.workers)):
                if not self.workers[avail]:
                    self.workers.pop(avail)
            self.squash_workers(self.name_to_worker_mapping(),
                                self.real_worker_availability())

    def get_suitable_worker(self, required_workers):
        """
        Returns suitable executor which has required amount of workers. Returns
        ``None`` if nothing is available.

        Actually it returns a tuple of worker and a count of workers available
        for utilization within a given pool. It may be more than
        ``required_workers`` but it can't be less.

        :param int required_workers: The amount of workers user requires.
        """
        with self.lock:
            min_available, suspected_workers = None, None
            for availability, workers in iteritems(self.workers):
                if availability >= required_workers:
                    if min_available is None or min_available < availability:
                        min_available = availability
                        suspected_workers = workers
            if min_available is not None:
                return suspected_workers.pop(), min_available
            return None, 0

    def worker_finished(self, worker, required_workers):
        """
        The callback used by
        :py:class:`streams.executors.mixins.PoolOfPoolsMixin`.
        """
        with self.lock:
            self.workers[required_workers].append(worker)

    def name_to_worker_mapping(self):
        """
        Maps worker names (the result of applying :py:func:`id` to the
        executor) to executor instances.
        """
        with self.lock:
            name_to_workers = {}
            for workers in itervalues(self.workers):
                name_to_workers.update(
                    (id(worker), worker) for worker in workers
                )
            return name_to_workers

    def real_worker_availability(self):
        """
        Returns mapping of the name for the executor and it real availability.
        Since :py:meth:`worker_finished` does not do any defragmentation of
        availability it may be possible that internal structure contains
        multiple controversial information about worker availability. This
        method is intended to restore the truth.
        """
        with self.lock:
            real_availability = defaultdict(lambda: [])
            for avail, workers in iteritems(self.workers):
                for wrk in workers:
                    real_availability[id(wrk)].append(avail)
            for name in iterkeys(real_availability):
                real_availability[name] = max(real_availability[name])

            availability_to_workers = defaultdict(lambda: [])
            for worker_name, avail in iteritems(real_availability):
                availability_to_workers[avail].append(worker_name)

            return availability_to_workers

    def squash_workers(self, names, avails):
        """
        Does actual squashing/defragmentation of internal structure.
        """
        self.workers = defaultdict(lambda: [])
        avails_to_traverse = set(iterkeys(avails))
        while avails_to_traverse:
            minimal_avail = min(avails_to_traverse)
            avails_to_traverse.discard(minimal_avail)
            workers = avails[minimal_avail]
            selected_worker = names[workers[0]]
            if len(workers) == 1:
                self.workers[minimal_avail] = [selected_worker]
            else:
                selected_worker.expand(minimal_avail * (len(workers) - 1))
                extended_avail = minimal_avail * len(workers)
                avails_to_traverse.add(extended_avail)
            avails.pop(minimal_avail)


class PoolOfPools(object):
    """
    Just a convenient interface to the set of multiple
    :py:class:`ExecutorPool` instances, nothing more.
    """

    @staticmethod
    def get_from_pool(pool, required_workers):
        """
        Fetches mapper from the pool.

        :param ExecutorPool pool:    The pool you want to fetch mapper from.
        :param int required_workers: The amount of workers you are requiring.
                                     It can be ``None`` then
                                     :py:meth:`ExecutorPool.get_any` would be
                                     executed.
        """
        if required_workers is None:
            return pool.get_any()
        return pool.get(required_workers)

    def __init__(self):
        self.parallels = ExecutorPool(ParallelExecutor)
        self.processes = ExecutorPool(ProcessPoolExecutor)
        self.default_count = cpu_count()

    def parallel(self, required_workers):
        """
        Fetches parallel executor mapper from the underlying
        :py:class:`ExecutorPool`.

        :param int required_workers: The amount of workers you are requiring.
                                     It can be ``None`` then
                                     :py:meth:`ExecutorPool.get_any` would be
                                     executed.
        """
        return self.get_from_pool(self.parallels, required_workers)

    def process(self, required_workers):
        """
        Fetches process executor mapper from the underlying
        :py:class:`ExecutorPool`.

        :param int required_workers: The amount of workers you are requiring.
                                     It can be ``None`` then
                                     :py:meth:`ExecutorPool.get_any` would be
                                     executed.
        """
        return self.get_from_pool(self.processes, required_workers)

    def get(self, kwargs):
        """
        Returns the mapper.

        :param dict kwargs: Keyword arguments for the mapper. Please checkout
                            :py:meth:`streams.Stream.map` documentation
                            to understand what this dict has to have.
        """
        if "parallel" in kwargs:
            parallel = kwargs["parallel"]
            if parallel in (1, True):
                return self.parallel(self.default_count)
            if parallel is not None:
                return self.parallel(parallel)

        if "process" in kwargs:
            process = kwargs["process"]
            if process in (1, True):
                return self.process(self.default_count)
            if process is not None:
                return self.process(process)
