from tendrl.ceph_integration.objects.ecprofile import ECProfile
from tendrl.commons.event import Event
from tendrl.commons import flows
from tendrl.commons.message import Message


class DeleteECProfile(flows.BaseFlow):
    obj = ECProfile

    def __init__(self, *args, **kwargs):
        super(DeleteECProfile, self).__init__(*args, **kwargs)

    def run(self):
        Event(
            Message(
                priority="info",
                publisher=NS.publisher_id,
                payload={
                    "message": "Starting deletion flow for ec-profile %s" %
                    (self.parameters['ECProfile.name'])
                    },
                job_id=self.parameters['job_id'],
                flow_id=self.parameters['flow_id'],
                cluster_id=NS.tendrl_context.integration_id,
            )
        )

        super(DeleteECProfile, self).run()
