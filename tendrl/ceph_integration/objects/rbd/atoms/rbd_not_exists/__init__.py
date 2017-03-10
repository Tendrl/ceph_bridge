import etcd

from tendrl.ceph_integration.manager.crud import Crud
from tendrl.commons import objects
from tendrl.ceph_integration.objects.rbd import Rbd
from tendrl.commons.event import Event
from tendrl.commons.message import Message


class RbdNotExists(objects.BaseAtom):
    obj = Rbd
    def __init__(self, *args, **kwargs):
        super(RbdNotExists, self).__init__(*args, **kwargs)

    def run(self):
        Event(
            Message(
                priority="info",
                publisher=NS.publisher_id,
                payload={
                    "message": "Checking if rbd: %s doesnt exist for pool %s" %
                    (self.parameters['Rbd.name'],
                     self.parameters['Rbd.pool_id'])
                },
                job_id=self.parameters['job_id'],
                flow_id=self.parameters['flow_id'],
                cluster_id=NS.tendrl_context.integration_id,
            )
        )
        try:
            Rbd(
                pool_id=self.parameters['Rbd.pool_id'],
                name=self.parameters['Rbd.name'],
            ).load()
        except etcd.EtcdKeyNotFound:
            return True

        Event(
            Message(
                priority="info",
                publisher=NS.publisher_id,
                payload={
                    "message": "Rbd: %s exists for pool %s" %
                    (self.parameters['Rbd.name'],
                     self.parameters['Rbd.pool_id'])
                },
                job_id=self.parameters['job_id'],
                flow_id=self.parameters['flow_id'],
                cluster_id=NS.tendrl_context.integration_id,
            )
        )
        return False
