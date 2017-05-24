from tendrl.ceph_integration.objects.pool import Pool
from tendrl.commons.event import Event
from tendrl.commons import flows
from tendrl.commons.message import Message


class UpdatePool(flows.BaseFlow):
    obj = Pool

    def __init__(self, *args, **kwargs):
        super(UpdatePool, self).__init__(*args, **kwargs)

    def run(self):
        Event(
            Message(
                priority="info",
                publisher=NS.publisher_id,
                payload={
                    "message": "Starting updation flow for pool-id %s" %
                    (self.parameters['Pool.pool_id'])
                    },
                job_id=self.parameters['job_id'],
                flow_id=self.parameters['flow_id'],
                cluster_id=NS.tendrl_context.integration_id,
            )
        )

        super(UpdatePool, self).run()
