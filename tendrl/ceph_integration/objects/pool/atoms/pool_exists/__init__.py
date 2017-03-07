import etcd

from tendrl.ceph_integration import objects
from tendrl.ceph_integration.objects.pool import Pool
from tendrl.commons.event import Event
from tendrl.commons.message import Message


class PoolExists(objects.CephIntegrationBaseAtom):
    obj = Pool
    def __init__(self, *args, **kwargs):
        super(PoolExists, self).__init__(*args, **kwargs)

    def run(self):
        Event(
            Message(
                priority="info",
                publisher=tendrl_ns.publisher_id,
                payload={
                    "message": "Checking if pool-id %s exists" %
                    self.parameters['Pool.pool_id']
                },
                job_id=self.parameters['job_id'],
                flow_id=self.parameters['flow_id'],
                cluster_id=tendrl_ns.tendrl_context.integration_id,
            )
        )

        try:
            fetched_pool = Pool(
                pool_id=self.parameters['Pool.pool_id']
            ).load()
        except etcd.EtcdKeyNotFound:
            Event(
                Message(
                    priority="warning",
                    publisher=tendrl_ns.publisher_id,
                    payload={
                        "message": "Pool with id %s doesnt exist" %
                        self.parameters['Pool.pool_id']
                    },
                    job_id=self.parameters['job_id'],
                    flow_id=self.parameters['flow_id'],
                    cluster_id=tendrl_ns.tendrl_context.integration_id,
                )
            )
            return False

        return True
