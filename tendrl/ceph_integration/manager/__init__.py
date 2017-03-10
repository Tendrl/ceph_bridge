import logging

import gevent.event
import signal

from tendrl.commons import TendrlNS
from tendrl.commons import manager
from tendrl import ceph_integration
from tendrl.ceph_integration import sds_sync
from tendrl.ceph_integration import central_store

LOG = logging.getLogger(__name__)


class CephIntegrationManager(manager.Manager):
    def __init__(self):
        self._complete = gevent.event.Event()
        super(
            CephIntegrationManager,
            self
        ).__init__(
            NS.state_sync_thread,
            NS.central_store_thread
        )


def main():
    ceph_integration.CephIntegrationNS()
    TendrlNS()

    NS.type = "sds"

    NS.central_store_thread =\
        central_store.CephIntegrationEtcdCentralStore()
    NS.state_sync_thread = sds_sync.CephIntegrationSdsSyncStateThread()

    NS.node_context.save()
    NS.tendrl_context.save()
    NS.ceph_integration.definitions.save()
    NS.ceph_integration.config.save()
    NS.publisher_id = "ceph_integration"

    m = CephIntegrationManager()
    m.start()

    complete = gevent.event.Event()

    def shutdown():
        LOG.info("Signal handler: stopping")
        complete.set()

    gevent.signal(signal.SIGTERM, shutdown)
    gevent.signal(signal.SIGINT, shutdown)

    while not complete.is_set():
        complete.wait(timeout=1)
