# -*- coding: utf-8 -*-


###############################################################################


from collections import defaultdict
from functools import partial
from multiprocessing import cpu_count
from threading import RLock

from six import iteritems, iterkeys, itervalues

from .executors import ParallelExecutor, ProcessPoolExecutor


###############################################################################


class ExecutorPool(object):

    def __init__(self, worker_class):
        self.worker_class = worker_class
        self.workers = defaultdict(lambda: [])
        self.lock = RLock()

    def get_any(self):
        with self.lock:
            return self.get(min(iterkeys(self.workers)))

    def get(self, required_workers):
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
        if not self.workers:
            return
        with self.lock:
            for avail in list(iterkeys(self.workers)):
                if not self.workers[avail]:
                    self.workers.pop(avail)
            self.squash_workers(self.name_to_worker_mapping(),
                                self.real_worker_availability())

    def get_suitable_worker(self, required_workers):
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
        with self.lock:
            self.workers[required_workers].append(worker)

    def name_to_worker_mapping(self):
        with self.lock:
            name_to_workers = {}
            for workers in itervalues(self.workers):
                name_to_workers.update(
                    (id(worker), worker) for worker in workers
                )
            return name_to_workers

    def real_worker_availability(self):
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

    @staticmethod
    def get_from_pool(pool, required_workers):
        if required_workers is None:
            return pool.get_any()
        return pool.get(required_workers)

    def __init__(self):
        self.parallels = ExecutorPool(ParallelExecutor)
        self.processes = ExecutorPool(ProcessPoolExecutor)
        self.default_count = cpu_count()

    def parallel(self, required_workers):
        return self.get_from_pool(self.parallels, required_workers)

    def process(self, required_workers):
        return self.get_from_pool(self.processes, required_workers)

    def get(self, kwargs):
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
