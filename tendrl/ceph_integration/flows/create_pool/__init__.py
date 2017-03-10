from tendrl.commons import flows
from tendrl.commons.event import Event
from tendrl.commons.message import Message


class CreatePool(flows.BaseFlow):
    def run(self):
        Event(
            Message(
                priority="info",
                publisher=NS.publisher_id,
                payload={
                    "message": "Starting creation flow for pool %s" %
                    self.parameters['Pool.poolname']
                },
                job_id=self.parameters['job_id'],
                flow_id=self.parameters['flow_id'],
                cluster_id=NS.tendrl_context.integration_id,
            )
        )
        super(CreatePool, self).run()
