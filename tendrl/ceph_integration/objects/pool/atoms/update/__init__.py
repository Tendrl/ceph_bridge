from tendrl.ceph_integration.manager.crud import Crud
from tendrl.ceph_integration.manager.exceptions import \
    RequestStateError
from tendrl.ceph_integration.objects.pool import Pool
from tendrl.commons.event import Event
from tendrl.commons.message import Message
from tendrl.commons import objects
from tendrl.commons.objects import AtomExecutionFailedError


class Update(objects.BaseAtom):
    obj = Pool

    def __init__(self, *args, **kwargs):
        super(Update, self).__init__(*args, **kwargs)

    def run(self):
        pool_id = self.parameters['Pool.pool_id']
        attrs = {}
        if 'Pool.pg_num' in self.parameters:
            fetched_obj = Pool(
                pool_id=self.parameters['Pool.pool_id']
            ).load()
            attrs['pg_num'] = self.parameters.get('Pool.pg_num')
            if attrs['pg_num'] <= int(fetched_obj.pg_num):
                raise AtomExecutionFailedError(
                    "New pg-num cannot be less than existing value"
                )
        if 'Pool.size' in self.parameters:
            attrs['size'] = self.parameters.get('Pool.size')
        if 'Pool.min_size' in self.parameters:
            attrs['min_size'] = self.parameters.get('Pool.min_size')
        if 'Pool.quota_enabled' in self.parameters and \
            self.parameters['Pool.quota_enabled'] is True:
            attrs['quota_max_objects'] = \
                self.parameters.get('Pool.quota_max_objects')
            attrs['quota_max_bytes'] = \
                self.parameters.get('Pool.quota_max_bytes')
        Event(
            Message(
                priority="info",
                publisher=NS.publisher_id,
                payload={
                    "message": "Updating details for pool-id %s."
                    " Attributes: %s" %
                    (self.parameters['Pool.pool_id'],
                     str(attrs))
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
                    priority="info",
                    publisher=NS.publisher_id,
                    payload={
                        "message": "Failed to update pool %s."
                        " Error: %s" % (self.parameters['Pool.pool_id'],
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
                    "message": "Pool %s successfully updated" %
                    (self.parameters['Pool.pool_id'])
                    },
                job_id=self.parameters['job_id'],
                flow_id=self.parameters['flow_id'],
                cluster_id=NS.tendrl_context.integration_id,
            )
        )

        return True
