from tendrl.ceph_integration.manager.crud import Crud
from tendrl.ceph_integration.manager.exceptions import \
    RequestStateError

from tendrl.commons.event import Event
from tendrl.commons.message import Message
from tendrl.commons import objects


class Rename(objects.BaseAtom):

    def __init__(self, *args, **kwargs):
        super(Rename, self).__init__(*args, **kwargs)

    def run(self):
        pool_id = self.parameters['Pool.pool_id']
        attrs = {}
        attrs['name'] = self.parameters.get('Pool.poolname')
        existing_name = NS._int.client.read(
            "clusters/%s/Pools/%s/pool_name" %
            (
                NS.tendrl_context.integration_id,
                self.parameters['Pool.pool_id']
            )
        ).value
        Event(
            Message(
                priority="info",
                publisher=NS.publisher_id,
                payload={
                    "message": "Renaming the pool:"
                               "%s with new name: %s" %
                    (existing_name,
                     self.parameters.get('Pool.poolname'))
                    },
                job_id=self.parameters['job_id'],
                flow_id=self.parameters['flow_id'],
                cluster_id=NS.tendrl_context.integration_id,
            )
        )

        crud = Crud()
        resp = crud.update("pool", pool_id, attrs)
        try:
            crud.sync_request_status(resp['request'])
        except RequestStateError as ex:
            Event(
                Message(
                    priority="error",
                    publisher=NS.publisher_id,
                    payload={
                        "message": "Failed to rename pool:"
                                   "%s with new name: %s"
                        " Error: %s" % (existing_name,
                                        self.parameters.get('Pool.poolname'),
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
                    "message": "Pool:"
                               "%s successfully renamed with new name: %s" %
                    (existing_name, self.parameters.get('Pool.poolname'))
                    },
                job_id=self.parameters['job_id'],
                flow_id=self.parameters['flow_id'],
                cluster_id=NS.tendrl_context.integration_id,
            )
        )

        return True
