import etcd
import gevent.event
import signal

from tendrl import ceph_integration

from tendrl.commons.event import Event
from tendrl.commons import manager
from tendrl.commons.message import Message
from tendrl.commons import TendrlNS


class CephIntegrationManager(manager.Manager):
    def __init__(self):
        self._complete = gevent.event.Event()
        super(
            CephIntegrationManager,
            self
        ).__init__(
            NS.state_sync_thread
        )


def main():
    ceph_integration.CephIntegrationNS()
    TendrlNS()

    NS.type = "sds"
    NS.publisher_id = "ceph_integration"

    from tendrl.ceph_integration import sds_sync

    NS.state_sync_thread = sds_sync.CephIntegrationSdsSyncStateThread()

    NS.node_context.save()

    # Check if Integration is part of any Tendrl imported/created sds cluster
    try:
        NS.tendrl_context = NS.tendrl_context.load()
        Event(
            Message(
                priority="info",
                publisher=NS.publisher_id,
                payload={"message": "Integration %s is part of sds cluster"
                                    % NS.tendrl_context.integration_id
                         }
            )
        )

    except etcd.EtcdKeyNotFound:
        Event(
            Message(
                priority="debug",
                publisher=NS.publisher_id,
                payload={"message": "Node %s is not part of any sds cluster" %
                                    NS.node_context.node_id
                         }
            )
        )
        raise Exception(
            "Integration cannot be started, "
            "please Import or Create sds cluster in Tendrl "
            "and include Node %s" % NS.node_context.node_id
        )
    if NS.tendrl_context.integration_id is None:
        Event(
            Message(
                priority="debug",
                publisher=NS.publisher_id,
                payload={"message": "Node %s is not part of any sds cluster" %
                                    NS.node_context.node_id
                         }
            )
        )
        raise Exception(
            "Integration cannot be started, "
            "please Import or Create sds cluster in Tendrl "
            "and include Node %s" % NS.node_context.node_id
        )

    NS.tendrl_context.save()
    NS.ceph.definitions.save()
    NS.ceph.config.save()
    
    if NS.config.data.get("with_internal_profiling", False):
        from tendrl.commons import profiler
        profiler.start()

    m = CephIntegrationManager()
    m.start()

    complete = gevent.event.Event()

    def shutdown():
        Event(
            Message(
                priority="info",
                publisher=NS.publisher_id,
                payload={"message": "Signal handler: stopping"}
            )
        )
        complete.set()

    gevent.signal(signal.SIGTERM, shutdown)
    gevent.signal(signal.SIGINT, shutdown)

    while not complete.is_set():
        complete.wait(timeout=1)
