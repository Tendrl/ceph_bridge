from tendrl.ceph_integration.manager.crud import Crud
from tendrl.ceph_integration.manager.exceptions import \
    RequestStateError
from tendrl.ceph_integration.objects.ecprofile import ECProfile
from tendrl.commons.event import Event
from tendrl.commons.message import Message
from tendrl.commons import objects


class Create(objects.BaseAtom):
    obj = ECProfile

    def __init__(self, *args, **kwargs):
        super(Create, self).__init__(*args, **kwargs)

    def run(self):
        if 'ECProfile.plugin' in self.parameters:
            plugin = self.parameters['ECProfile.plugin']
        else:
            plugin = 'jerasure'

        if 'ECProfile.directory' in self.parameters:
            directory = self.parameters.get('ECProfile.directory')
        else:
            directory = "/usr/lib/ceph/erasure-code"

        attrs = dict(name=self.parameters['ECProfile.name'],
                     k=self.parameters['ECProfile.k'],
                     m=self.parameters['ECProfile.m'],
                     plugin=plugin,
                     directory=directory
                     )
        Event(
            Message(
                priority="info",
                publisher=NS.publisher_id,
                payload={
                    "message": "Creating ec-profile %s" %
                    self.parameters['ECProfile.name'],
                },
                job_id=self.parameters['job_id'],
                flow_id=self.parameters['flow_id'],
                cluster_id=NS.tendrl_context.integration_id,
            )
        )

        crud = Crud()
        resp = crud.create("ec_profile", attrs)
        try:
            crud.sync_request_status(resp['request'])
        except RequestStateError as ex:
            Event(
                Message(
                    priority="info",
                    publisher=NS.publisher_id,
                    payload={
                        "message": "Failed to create ec-profile %s."
                        " Error: %s" % (self.parameters['ECProfile.name'],
                                        ex)
                    },
                    job_id=self.parameters['job_id'],
                    flow_id=self.parameters['flow_id'],
                    cluster_id=NS.tendrl_context.integration_id,
                )
            )
            return False

        Event(
            Message(
                priority="info",
                publisher=NS.publisher_id,
                payload={
                    "message": "Successfully created ec-profile %s" %
                    self.parameters['ECProfile.name'],
                },
                job_id=self.parameters['job_id'],
                flow_id=self.parameters['flow_id'],
                cluster_id=NS.tendrl_context.integration_id,
            )
        )

        return True
