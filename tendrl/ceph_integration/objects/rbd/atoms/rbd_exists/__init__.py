import etcd

from tendrl.ceph_integration.manager.crud import Crud
from tendrl.ceph_integration import objects
from tendrl.ceph_integration.objects.rbd import Rbd
from tendrl.commons.event import Event
from tendrl.commons.message import Message


class RbdExists(objects.CephIntegrationBaseAtom):
    obj = Rbd
    def __init__(self, *args, **kwargs):
        super(RbdExists, self).__init__(*args, **kwargs)

    def run(self):
        Event(
            Message(
                priority="info",
                publisher=tendrl_ns.publisher_id,
                payload={
                    "message": "Checking if rbd: %s exists for pool %s" %
                    (self.parameters['Rbd.name'],
                     self.parameters['Rbd.pool_id'])
                },
                job_id=self.parameters['job_id'],
                flow_id=self.parameters['flow_id'],
                cluster_id=tendrl_ns.tendrl_context.integration_id,
            )
        )
        try:
            fetched_rbd = Rbd(
                pool_id=self.parameters['Rbd.pool_id'],
                name=self.parameters['Rbd.name'],
            ).load()
        except etcd.EtcdKeyNotFound:
            Event(
                Message(
                    priority="info",
                    publisher=tendrl_ns.publisher_id,
                    payload={
                        "message": "Rbd: %s exists for pool %s" %
                        (self.parameters['Rbd.name'],
                         self.parameters['Rbd.pool_id'])
                    },
                    job_id=self.parameters['job_id'],
                    flow_id=self.parameters['flow_id'],
                    cluster_id=tendrl_ns.tendrl_context.integration_id,
                )
            )
            return False

        return True
