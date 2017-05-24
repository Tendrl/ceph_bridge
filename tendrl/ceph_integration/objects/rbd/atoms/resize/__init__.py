from tendrl.ceph_integration.manager.crud import Crud
from tendrl.ceph_integration.manager.exceptions import \
    RequestStateError
from tendrl.ceph_integration.objects.rbd import Rbd
from tendrl.commons.event import Event
from tendrl.commons.message import Message
from tendrl.commons import objects


class Resize(objects.BaseAtom):
    obj = Rbd

    def __init__(self, *args, **kwargs):
        super(Resize, self).__init__(*args, **kwargs)

    def run(self):
        attrs = dict(pool_id=self.parameters['Rbd.pool_id'],
                     size=str(self.parameters['Rbd.size']))
        Event(
            Message(
                priority="info",
                publisher=NS.publisher_id,
                payload={
                    "message": "Re-sizing rbd %s on pool %s to %s" %
                    (self.parameters['Rbd.name'],
                     self.parameters['Rbd.pool_id'],
                     self.parameters['Rbd.size'])
                },
                job_id=self.parameters['job_id'],
                flow_id=self.parameters['flow_id'],
                cluster_id=NS.tendrl_context.integration_id,
            )
        )

        crud = Crud()
        resp = crud.update("rbd", self.parameters['Rbd.name'], attrs)
        try:
            crud.sync_request_status(resp['request'])
        except RequestStateError as ex:
            Event(
                Message(
                    priority="info",
                    publisher=NS.publisher_id,
                    payload={
                        "message": "Failed to resize rbd %s."
                        " Error: %s" % (self.parameters['Rbd.name'],
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
                    "message": "Successfully re-sized rbd %s on pool-id %s to "
                    "%s" % (self.parameters['Rbd.name'],
                            self.parameters['Rbd.pool_id'],
                            self.parameters['Rbd.size'])
                },
                job_id=self.parameters['job_id'],
                flow_id=self.parameters['flow_id'],
                cluster_id=NS.tendrl_context.integration_id,
            )
        )

        return True
