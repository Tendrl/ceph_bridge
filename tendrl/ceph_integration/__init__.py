__version__ = '1.1'
try:
    from gevent import monkey
except ImportError:
    pass
else:
    monkey.patch_all()

from tendrl.commons import etcdobj
from tendrl.commons import log
from tendrl.commons import CommonNS

from tendrl.ceph_integration.flows.create_pool import CreatePool
from tendrl.ceph_integration.objects.config import Config
from tendrl.ceph_integration.objects.definition import Definition
from tendrl.ceph_integration.objects.event import Event
from tendrl.ceph_integration.objects.pool import Pool
from tendrl.ceph_integration.objects.pool.atoms.create import Create
from tendrl.ceph_integration.objects.pool.atoms.delete import Delete
from tendrl.ceph_integration.objects.pool.flows.delete import DeletePool
from tendrl.ceph_integration.objects.server import Server
from tendrl.ceph_integration.objects.service import service
from tendrl.ceph_integration.objects.sync_object import SyncObject
from tendrl.ceph_integration.objects.tendrl_context import TendrlContext


class CephIntegrationNS(CommonNS):
    def __init__(self):

        # Create the "tendrl_ns.ceph_integration" namespace
        self.to_str = "tendrl.ceph_integration"
        self.type = 'ceph'
        super(CephIntegrationNS, self).__init__()

    def setup_initial_objects(self):
        # Definitions
        tendrl_ns.definitions = tendrl_ns.ceph_integration.objects.Definition()

        # Config
        tendrl_ns.config = tendrl_ns.ceph_integration.objects.Config()

        # NodeContext
        tendrl_ns.tendrl_context =\
         tendrl_ns.ceph_integration.objects.TendrlContext()

        # etcd_orm
        etcd_kwargs = {'port': tendrl_ns.config.data['etcd_port'],
                       'host': tendrl_ns.config.data["etcd_connection"]}
        tendrl_ns.etcd_orm = etcdobj.Server(etcd_kwargs=etcd_kwargs)

        log.setup_logging(
             tendrl_ns.config.data['log_cfg_path'],
        )


import __builtin__
__builtin__.tendrl_ns = CephIntegrationNS()
