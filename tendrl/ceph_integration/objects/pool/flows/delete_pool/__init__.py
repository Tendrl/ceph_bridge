from tendrl.ceph_integration import objects
from tendrl.ceph_integration.flows import CephIntegrationBaseFlow
from tendrl.ceph_integration.objects.pool import Pool
from tendrl.commons.event import Event
from tendrl.commons.message import Message


class DeletePool(CephIntegrationBaseFlow):
    obj = Pool
    def __init__(self, *args, **kwargs):
        super(DeletePool, self).__init__(*args, **kwargs)

    def run(self):
        Event(
            Message(
                priority="info",
                publisher=tendrl_ns.publisher_id,
                payload={
                    "message": "Starting deletion flow for pool-id %s" %
                    (self.parameters['Pool.pool_id'])
                    },
                job_id=self.job_id,
                flow_id=self.uuid,
                cluster_id=tendrl_ns.tendrl_context.integration_id,
            )
        )
        super(DeletePool, self).run()
