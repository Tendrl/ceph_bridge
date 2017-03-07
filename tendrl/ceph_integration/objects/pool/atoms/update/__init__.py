from tendrl.ceph_integration.manager.crud import Crud
from tendrl.ceph_integration import objects
from tendrl.ceph_integration.objects.pool import Pool
from tendrl.commons.event import Event
from tendrl.commons.message import Message
from tendrl.commons.objects.atoms import AtomExecutionFailedError


class Update(objects.CephIntegrationBaseAtom):
    obj = Pool
    def __init__(self, *args, **kwargs):
        super(Update, self).__init__(*args, **kwargs)

    def run(self):
        pool_id = self.parameters['Pool.pool_id']
        attrs = {}
        if 'Pool.poolname' in self.parameters:
            attrs['name'] = self.parameters.get('Pool.poolname')
        if 'Pool.pg_num' in self.parameters:
            fetched_obj = Pool(
                pool_id=self.parameters['Pool.pool_id']
            ).load()
            attrs['pg_num'] = self.parameters.get('Pool.pg_num')
            if attrs['pg_num'] <= fetched_obj.pg_num:
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
                publisher=tendrl_ns.publisher_id,
                payload={
                    "message": "Updating details for pool-id %s."
                    " Attributes: %s" %
                    (self.parameters['Pool.pool_id'],
                     str(attrs))
                    },
                job_id=self.parameters['job_id'],
                flow_id=self.parameters['flow_id'],
                cluster_id=tendrl_ns.tendrl_context.integration_id,
            )
        )

        crud = Crud()
        ret_val = crud.update("pool", pool_id, attrs)
        if ret_val['response'] is not None and \
            ret_val['response']['error'] is True:
            Event(
                Message(
                    priority="info",
                    publisher=tendrl_ns.publisher_id,
                    payload={
                        "message": "Failed to update pool %s."
                        " Error: %s" % (self.parameters['Pool.pool_id'],
                                        ret_val['error_status'])
                    },
                    job_id=self.parameters['job_id'],
                    flow_id=self.parameters["flow_id"],
                    cluster_id=tendrl_ns.tendrl_context.integration_id,
                )
            )
            return False

        Event(
            Message(
                priority="info",
                publisher=tendrl_ns.publisher_id,
                payload={
                    "message": "Pool %s successfully updated" %
                    (self.parameters['Pool.pool_id'])
                    },
                job_id=self.parameters['job_id'],
                flow_id=self.parameters['flow_id'],
                cluster_id=tendrl_ns.tendrl_context.integration_id,
            )
        )

        return True
