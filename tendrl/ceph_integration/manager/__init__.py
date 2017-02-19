import gevent.event
import signal

from tendrl.ceph_integration import sds_sync
from tendrl.ceph_integration import central_store

from tendrl.commons.event import Event
from tendrl.commons.message import Message
from tendrl.commons import manager


class CephIntegrationManager(manager.Manager):
    def __init__(self):
        self._complete = gevent.event.Event()
        super(
            CephIntegrationManager,
            self
        ).__init__(
            tendrl_ns.state_sync_thread,
            tendrl_ns.central_store_thread
        )


def main():
    tendrl_ns.publisher_id = "ceph_integration"
    tendrl_ns.central_store_thread =\
        central_store.CephIntegrationEtcdCentralStore()
    tendrl_ns.state_sync_thread = sds_sync.CephIntegrationSdsSyncStateThread()

    tendrl_ns.node_context.save()
    tendrl_ns.tendrl_context.save()
    tendrl_ns.definitions.save()
    tendrl_ns.config.save()

    m = CephIntegrationManager()
    m.start()

    complete = gevent.event.Event()

    def shutdown():
        Event(
            Message(
                priority="info",
                publisher=tendrl_ns.publisher_id,
                payload={"message": "Signal handler: stopping"}
            )
        )
        complete.set()

    gevent.signal(signal.SIGTERM, shutdown)
    gevent.signal(signal.SIGINT, shutdown)

    while not complete.is_set():
        complete.wait(timeout=1)
