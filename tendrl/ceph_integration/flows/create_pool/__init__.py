from tendrl.ceph_integration import flows
from tendrl.commons.event import Event
from tendrl.commons.message import Message


class CreatePool(flows.CephIntegrationBaseFlow):
    def run(self):
        Event(
            Message(
                priority="info",
                publisher=tendrl_ns.publisher_id,
                payload={
                    "message": "Starting creation flow for pool %s" %
                    self.parameters['Pool.poolname']
                },
                job_id=self.job_id,
                flow_id=self.uuid,
                cluster_id=tendrl_ns.tendrl_context.integration_id,
            )
        )
        super(CreatePool, self).run()
