from tendrl.commons import objects
from tendrl.ceph_integration.objects.rbd import Rbd
from tendrl.ceph_integration.manager.rbd_crud import RbdCrud
from tendrl.commons.event import Event
from tendrl.commons.message import Message


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
        ret_val = crud.delete_rbd(
            pool_id,
            rbd_name
        )
        if ret_val['response'] is not None and \
            ret_val['response']['error'] is True:
            Event(
                Message(
                    priority="info",
                    publisher=NS.publisher_id,
                    payload={
                        "message": "Failed to delete rbd %s."
                        " Error: %s" % (self.parameters['Rbd.name'],
                                        ret_val['error_status'])
                    },
                    job_id=self.parameters['job_id'],
                    flow_id=self.parameters['flow_id'],
                    cluster_id=NS.tendrl_context.integration_id,
                )
            )
            return False

        NS.etcd_orm.client.delete(
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
