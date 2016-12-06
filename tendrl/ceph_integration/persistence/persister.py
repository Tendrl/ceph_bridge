import datetime
import logging

import gevent.event
import gevent.greenlet
import gevent.queue

from tendrl.ceph_integration.config import TendrlConfig
from tendrl.ceph_integration.persistence.sync_objects import SyncObject
from tendrl.common.etcdobj.etcdobj import Server as etcd_server


config = TendrlConfig()
LOG = logging.getLogger(__name__)

CLUSTER_MAP_RETENTION = datetime.timedelta(
    seconds=int(config.get('ceph_integration', 'cluster_map_retention')))


class deferred_call(object):

    def __init__(self, fn, args, kwargs):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def call_it(self):
        self.fn(*self.args, **self.kwargs)


class Persister(gevent.greenlet.Greenlet):
    """Asynchronously persist a queue of updates.  This is for use by classes

    that maintain the primary copy of state in memory, but also lazily update

    the DB so that they can recover from it on restart.

    """

    def __init__(self):
        super(Persister, self).__init__()

        self._queue = gevent.queue.Queue()
        self._complete = gevent.event.Event()

        self._store = self.get_store()

    def __getattribute__(self, item):
        """Wrap functions with logging

        """
        if item.startswith('_'):
            return object.__getattribute__(self, item)
        else:
            try:
                return object.__getattribute__(self, item)
            except AttributeError:
                try:
                    attr = object.__getattribute__(self, "_%s" % item)
                    if callable(attr):
                        def defer(*args, **kwargs):
                            dc = deferred_call(attr, args, kwargs)
                            try:
                                dc.call_it()
                            except Exception as ex:
                                LOG.exception(
                                    "Persister exception persisting"
                                    " data: %s" % (dc.fn,)
                                )
                                LOG.exception(ex)
                        return defer
                    else:
                        return object.__getattribute__(self, item)
                except AttributeError:
                    return object.__getattribute__(self, item)

    def _update_sync_object(self,
                            updated,
                            fsid,
                            name,
                            sync_type,
                            version,
                            when,
                            data,
                            cluster_id):
        self._store.save(
            SyncObject(
                updated=updated,
                fsid=fsid,
                cluster_name=name,
                sync_type=sync_type,
                version=version,
                when=when,
                data=data,
                cluster_id=cluster_id
            )
        )

    def _create_server(self, server):
        self._store.save(server)

    def _create_service(self, service):
        self._store.save(service)

    def _save_events(self, events):
        for event in events:
            self._store.save(event)

    def update_tendrl_context(self, context):
        self._store.save(context)

    def update_tendrl_definitions(self, definition):
        self._store.save(definition)

    def update_pool(self, pool):
        self._store.save(pool)

    def _run(self):
        LOG.info("Persister listening")

        while not self._complete.is_set():
            gevent.sleep(0.1)
            pass

    def stop(self):
        self._complete.set()

    def get_store(self):
        etcd_kwargs = {'port': int(config.get("common", "etcd_port")),
                       'host': config.get("common", "etcd_connection")}
        return etcd_server(etcd_kwargs=etcd_kwargs)
