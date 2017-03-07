from tendrl.ceph_integration import objects
from tendrl.ceph_integration.flows import CephIntegrationBaseFlow
from tendrl.ceph_integration.objects.ecprofile import ECProfile
from tendrl.commons.event import Event
from tendrl.commons.message import Message


class DeleteECProfile(CephIntegrationBaseFlow):
    obj = ECProfile
    def __init__(self, *args, **kwargs):
        super(DeleteECProfile, self).__init__(*args, **kwargs)

    def run(self):
        Event(
            Message(
                priority="info",
                publisher=tendrl_ns.publisher_id,
                payload={
                    "message": "Starting deletion flow for ec-profile %s" %
                    (self.parameters['ECProfile.name'])
                    },
                job_id=self.job_id,
                flow_id=self.uuid,
                cluster_id=tendrl_ns.tendrl_context.integration_id,
            )
        )

        super(DeleteECProfile, self).run()
