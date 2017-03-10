import etcd

from tendrl.commons import objects
from tendrl.ceph_integration.objects.pool import Pool
from tendrl.commons.event import Event
from tendrl.commons.message import Message


class PoolNotExists(objects.BaseAtom):
    obj = Pool
    def __init__(self, *args, **kwargs):
        super(PoolNotExists, self).__init__(*args, **kwargs)

    def run(self):
        Event(
            Message(
                priority="info",
                publisher=NS.publisher_id,
                payload={
                    "message": "Checking if pool-id %s doesnt exist" %
                    self.parameters['Pool.pool_id']
                },
                job_id=self.parameters['job_id'],
                flow_id=self.parameters['flow_id'],
                cluster_id=NS.tendrl_context.integration_id,
            )
        )

        try:
            Pool(
                pool_id=self.parameters['Pool.pool_id']
            ).load()
        except etcd.EtcdKeyNotFound:
            return True

        return False
