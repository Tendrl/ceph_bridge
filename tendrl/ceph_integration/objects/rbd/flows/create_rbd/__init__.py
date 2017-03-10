from tendrl.commons import flows
from tendrl.ceph_integration.objects.rbd import Rbd
from tendrl.commons.event import Event
from tendrl.commons.message import Message


class CreateRbd(flows.BaseFlow):
    obj = Rbd
    def __init__(self, *args, **kwargs):
        super(CreateRbd, self).__init__(*args, **kwargs)

    def run(self):
        Event(
            Message(
                priority="info",
                publisher=NS.publisher_id,
                payload={
                    "message": "Starting creation flow for rbd %s" %
                    (self.parameters['Rbd.name'])
                    },
                job_id=self.parameters['job_id'],
                flow_id=self.parameters['flow_id'],
                cluster_id=NS.tendrl_context.integration_id,
            )
        )

        super(CreateRbd, self).run()
