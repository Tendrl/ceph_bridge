import gc
import greenlet
import logging
import signal
import traceback

import gevent.event
import gevent.greenlet
import time

from tendrl.common import log

from tendrl.ceph_integration import ceph
from tendrl.ceph_integration.manager.cluster_monitor import ClusterMonitor
from tendrl.ceph_integration.manager.rpc import EtcdThread
from tendrl.ceph_integration.manager.tendrl_definitions_ceph import \
    data as def_data
from tendrl.ceph_integration.manager import utils
from tendrl.ceph_integration.persistence.persister import Persister
from tendrl.ceph_integration.persistence.tendrl_context import TendrlContext
from tendrl.ceph_integration.persistence.tendrl_definitions import \
    TendrlDefinitions


from tendrl.ceph_integration.config import TendrlConfig
config = TendrlConfig()


LOG = logging.getLogger(__name__)


class TopLevelEvents(gevent.greenlet.Greenlet):

    def __init__(self, manager):
        super(TopLevelEvents, self).__init__()

        self._manager = manager
        self._complete = gevent.event.Event()

    def stop(self):
        self._complete.set()

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
                                self._manager.on_discovery(cluster_data)
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


class Manager(object):
    """Manage a collection of ClusterMonitors.

    Subscribe to ceph/cluster events, and create a ClusterMonitor

    for any FSID we haven't seen before.

    """

    def __init__(self, cluster_id):
        self._complete = gevent.event.Event()
        self.cluster_id = cluster_id
        self._user_request_thread = EtcdThread(self)
        self._discovery_thread = TopLevelEvents(self)
        self.persister = Persister()

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

    def stop(self):
        LOG.info("%s stopping" % self.__class__.__name__)
        for monitor in self.clusters.values():
            monitor.stop()
        self._user_request_thread.stop()
        self._discovery_thread.stop()
        # self.eventer.stop()

    def _expunge(self, fsid):
        pass

    def _recover(self):
        LOG.debug("Recovered server")
        pass

    def start(self):
        LOG.info("%s starting" % self.__class__.__name__)
        self._user_request_thread.start()
        self._discovery_thread.start()
        self.persister.start()
        # self.eventer.start()

        # self.servers.start()

    def join(self):
        LOG.info("%s joining" % self.__class__.__name__)
        self._user_request_thread.join()
        self._discovery_thread.join()
        self.persister.join()
        # self.eventer.join()
        # self.servers.join()
        for monitor in self.clusters.values():
            monitor.join()

    def on_discovery(self, heartbeat_data):
        LOG.info("on_discovery: {0}".format(heartbeat_data['fsid']))
        cluster_monitor = ClusterMonitor(
            heartbeat_data['fsid'],
            heartbeat_data['name'],
            self.persister, self
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
        self.persister.update_tendrl_context(
            TendrlContext(
                updated=str(time.time()),
                node_id=utils.get_node_context(),
                sds_name="ceph",
                cluster_id=cluster_id,
                sds_version=utils.get_sds_version()
            )
        )

        self.persister.update_tendrl_definitions(TendrlDefinitions(
            updated=str(time.time()), data=def_data, cluster_id=cluster_id))


def dump_stacks():
    """This is for use in debugging, especially using manhole

    """
    for ob in gc.get_objects():
        if not isinstance(ob, greenlet.greenlet):
            continue
        if not ob:
            continue
        LOG.error(''.join(traceback.format_stack(ob.gr_frame)))


def main():
    log.setup_logging(
        config.get('ceph_integration', 'log_cfg_path'),
        config.get('ceph_integration', 'log_level')
    )

    cluster_id = utils.get_tendrl_context()
    if not cluster_id:
        LOG.error("Could not find cluster_id")
        exit(1)

    m = Manager(cluster_id)
    m.start()

    complete = gevent.event.Event()

    def shutdown():
        LOG.info("Signal handler: stopping")
        complete.set()

    gevent.signal(signal.SIGTERM, shutdown)
    gevent.signal(signal.SIGINT, shutdown)

    while not complete.is_set():
        complete.wait(timeout=1)
