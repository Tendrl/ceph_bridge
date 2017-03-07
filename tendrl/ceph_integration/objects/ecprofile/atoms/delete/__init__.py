from tendrl.ceph_integration.manager.crud import Crud
from tendrl.ceph_integration import objects
from tendrl.ceph_integration.objects.ecprofile import ECProfile
from tendrl.commons.event import Event
from tendrl.commons.message import Message


class Delete(objects.CephIntegrationBaseAtom):
    obj = ECProfile
    def __init__(self, *args, **kwargs):
        super(Delete, self).__init__(*args, **kwargs)

    def run(self):
        Event(
            Message(
                priority="info",
                publisher=tendrl_ns.publisher_id,
                payload={
                    "message": "Deleting ec-profile %s" %
                    self.parameters['ECProfile.name'],
                },
                job_id=self.parameters['job_id'],
                flow_id=self.parameters["flow_id"],
                cluster_id=tendrl_ns.tendrl_context.integration_id,
            )
        )

        crud = Crud()
        ret_val = crud.delete("ec_profile", self.parameters['ECProfile.name'])
        if ret_val['response'] is not None and \
            ret_val['response']['error'] is True:
            Event(
                Message(
                    priority="info",
                    publisher=tendrl_ns.publisher_id,
                    payload={
                        "message": "Failed to delete ec-profile %s."
                        " Error: %s" % (self.parameters['ECProfile.name'],
                                        ret_val['error_status'])
                    },
                    job_id=self.parameters['job_id'],
                    flow_id=self.parameters["flow_id"],
                    cluster_id=tendrl_ns.tendrl_context.integration_id,
                )
            )
            return False

        tendrl_ns.etcd_orm.client.delete(
            "clusters/%s/ECProfiles/%s" % (
                tendrl_ns.tendrl_context.integration_id,
                self.parameters['ECProfile.name']
            ),
            recursive=True
        )
        Event(
            Message(
                priority="info",
                publisher=tendrl_ns.publisher_id,
                payload={
                    "message": "Deleted ec-profile %s" %
                    self.parameters['ECProfile.name'],
                },
                job_id=self.parameters['job_id'],
                flow_id=self.parameters["flow_id"],
                cluster_id=tendrl_ns.tendrl_context.integration_id,
            )
        )

        return True
