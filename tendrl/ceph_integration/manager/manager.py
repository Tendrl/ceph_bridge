import gevent.event
import logging
import signal
import sys
import time

from tendrl.ceph_integration import ceph
from tendrl.ceph_integration.manager.cluster_monitor import ClusterMonitor
from tendrl.ceph_integration.manager.tendrl_definitions_ceph import \
    data as def_data
from tendrl.ceph_integration.manager import utils
from tendrl.ceph_integration.persistence.persister import \
    CephIntegrationEtcdPersister
from tendrl.ceph_integration.persistence.tendrl_context import TendrlContext
from tendrl.ceph_integration.persistence.tendrl_definitions import \
    TendrlDefinitions
from tendrl.commons.config import TendrlConfig
from tendrl.commons.log import setup_logging
from tendrl.commons.manager.manager import Manager
from tendrl.commons.manager.manager import SyncStateThread

config = TendrlConfig("ceph-integration", "/etc/tendrl/tendrl.conf")

LOG = logging.getLogger(__name__)


class CephIntegrationSyncStateThread(SyncStateThread):

    def __init__(self, manager, cluster_id):
        super(CephIntegrationSyncStateThread, self).__init__(manager)

        self._manager = manager
        self._complete = gevent.event.Event()
        self.cluster_id = cluster_id

    def _run(self):
        LOG.info("%s running" % self.__class__.__name__)

        while not self._complete.is_set():
            data = ceph.heartbeat(heartbeat_type="cluster", discover=True)
            if data is not None:
                for tag, cluster_data in data.iteritems():
                    try:
                        if tag.startswith("ceph/cluster/"):
                            if not cluster_data[
                                    'fsid'
                            ] in self._manager.clusters:
                                self._manager.on_pull(
                                    cluster_data,
                                    self.cluster_id
                                )
                            else:
                                LOG.debug(
                                    "%s: heartbeat from existing"
                                    " cluster %s" % (
                                        self.__class__.__name__,
                                        cluster_data['fsid']
                                    )
                                )
                        else:
                            # This does not concern us, ignore it
                            LOG.debug("TopLevelEvents: ignoring %s" % tag)
                            pass
                    except Exception:
                        LOG.exception(
                            "Exception handling message tag=%s" % tag)
            gevent.sleep(3)

        LOG.info("%s complete" % self.__class__.__name__)


class CephIntegrationManager(Manager):
    def __init__(self, cluster_id):
        self._complete = gevent.event.Event()
        self.cluster_id = cluster_id
        super(
            CephIntegrationManager,
            self
        ).__init__(
            "sds",
            cluster_id,
            config,
            CephIntegrationSyncStateThread(self, cluster_id),
            CephIntegrationEtcdPersister(config),
            "clusters/%s/definitions/data" % cluster_id
        )
        # FSID to ClusterMonitor
        self.clusters = {}

        # Generate events on state changes
        # self.eventer = Eventer(self)

        # Handle all ceph/server messages after cluster is discovered to
        # maintain etcd schema
        # self.servers = ServerMonitor(self.persister, self.eventer)
        self.register_to_cluster(cluster_id)

    def delete_cluster(self, fs_id):
        """Note that the cluster will pop right back again if it's

        still sending heartbeats.

        """
        victim = self.clusters[fs_id]
        victim.stop()
        victim.done.wait()
        del self.clusters[fs_id]

        self._expunge(fs_id)

    def join(self):
        super(self).join()
        for monitor in self.clusters.values():
            monitor.join()

    def on_pull(self, heartbeat_data, cluster_id):
        LOG.info("on_discovery: {0}".format(heartbeat_data['fsid']))
        cluster_monitor = ClusterMonitor(
            heartbeat_data['fsid'],
            heartbeat_data['name'],
            self.persister_thread, self
        )
        self.clusters[heartbeat_data['fsid']] = cluster_monitor
        utils.set_fsid(heartbeat_data['fsid'])
        # Run before passing on the heartbeat, because otherwise the
        # syncs resulting from the heartbeat might not be received
        # by the monitor.
        cluster_monitor.start()
        # Wait for ClusterMonitor to start accepting events before asking it
        # to do anything
        cluster_monitor.ready()
        cluster_monitor.on_heartbeat(heartbeat_data['id'], heartbeat_data)

    def register_to_cluster(self, cluster_id):
        self.persister_thread.update_tendrl_context(
            TendrlContext(
                updated=str(time.time()),
                node_id=utils.get_node_context(),
                sds_name="ceph",
                cluster_id=cluster_id,
                sds_version=utils.get_sds_version()
            )
        )

        self.persister_thread.update_tendrl_definitions(TendrlDefinitions(
            updated=str(time.time()), data=def_data, cluster_id=cluster_id))


def main():
    setup_logging(
        config.get('ceph-integration', 'log_cfg_path'),
        config.get('ceph-integration', 'log_level')
    )
    if sys.argv:
        if len(sys.argv) > 1:
            if "cluster-id" in sys.argv[1]:
                cluster_id = sys.argv[2]
                utils.set_tendrl_context(cluster_id)

    m = CephIntegrationManager(utils.get_tendrl_context())
    m.start()

    complete = gevent.event.Event()

    def shutdown():
        LOG.info("Signal handler: stopping")
        complete.set()

    gevent.signal(signal.SIGTERM, shutdown)
    gevent.signal(signal.SIGINT, shutdown)

    while not complete.is_set():
        complete.wait(timeout=1)
