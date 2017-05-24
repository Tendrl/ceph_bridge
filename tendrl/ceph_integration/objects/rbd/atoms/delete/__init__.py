from tendrl.ceph_integration.manager.exceptions import \
    RequestStateError
from tendrl.ceph_integration.manager.rbd_crud import RbdCrud
from tendrl.ceph_integration.objects.rbd import Rbd
from tendrl.commons.event import Event
from tendrl.commons.message import Message
from tendrl.commons import objects


class Delete(objects.BaseAtom):
    obj = Rbd

    def __init__(self, *args, **kwargs):
        super(Delete, self).__init__(*args, **kwargs)

    def run(self):
        pool_id = self.parameters['Rbd.pool_id']
        rbd_name = self.parameters['Rbd.name']

        Event(
            Message(
                priority="info",
                publisher=NS.publisher_id,
                payload={
                    "message": "Deleting rbd %s on pool %s" %
                    (self.parameters['Rbd.name'],
                     self.parameters['Rbd.pool_id'])
                },
                job_id=self.parameters['job_id'],
                flow_id=self.parameters['flow_id'],
                cluster_id=NS.tendrl_context.integration_id,
            )
        )

        crud = RbdCrud()
        resp = crud.delete_rbd(
            pool_id,
            rbd_name
        )
        try:
            crud.sync_request_status(resp['request'])
        except RequestStateError as ex:
            Event(
                Message(
                    priority="info",
                    publisher=NS.publisher_id,
                    payload={
                        "message": "Failed to delete rbd %s."
                        " Error: %s" % (self.parameters['Rbd.name'],
                                        ex)
                    },
                    job_id=self.parameters['job_id'],
                    flow_id=self.parameters['flow_id'],
                    cluster_id=NS.tendrl_context.integration_id,
                )
            )
            return False

        NS._int.wclient.delete(
            "clusters/%s/Pools/%s/Rbds/%s" % (
                NS.tendrl_context.integration_id,
                self.parameters['Rbd.pool_id'],
                self.parameters['Rbd.name']
            ),
            recursive=True
        )
        Event(
            Message(
                priority="info",
                publisher=NS.publisher_id,
                payload={
                    "message": "Deleted rbd %s on pool-id %s" %
                    (self.parameters['Rbd.name'],
                     self.parameters['Rbd.pool_id'])
                },
                job_id=self.parameters['job_id'],
                flow_id=self.parameters['flow_id'],
                cluster_id=NS.tendrl_context.integration_id,
            )
        )

        return True
