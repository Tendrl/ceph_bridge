from tendrl.commons import objects
from tendrl.ceph_integration.objects.pool import Pool
from tendrl.commons.event import Event
from tendrl.commons.message import Message
from tendrl.commons.objects import AtomExecutionFailedError


class ValidUpdateParameters(objects.BaseAtom):
    obj = Pool
    def __init__(self, *args, **kwargs):
        super(ValidUpdateParameters, self).__init__(*args, **kwargs)

    def run(self):
        Event(
            Message(
                priority="info",
                publisher=NS.publisher_id,
                payload={
                    "message": "Checking if update parameters are valid"
                },
                job_id=self.parameters['job_id'],
                flow_id=self.parameters['flow_id'],
                cluster_id=NS.tendrl_context.integration_id,
            )
        )

        if 'Pool.poolname' in self.parameters and \
            ('Pool.pg_num' in self.parameters or
             'Pool.size' in self.parameters or
             'Pool.pg_num' in self.parameters or
             'Pool.min_size' in self.parameters or
             'Pool.quota_enabled' in self.parameters):
            Event(
                Message(
                    priority="info",
                    publisher=NS.publisher_id,
                    payload={
                        "message": "Invalid combination of pool update parameters. "
                        "Pool name shouldnt be updated with other parameters."
                    },
                    job_id=self.parameters['job_id'],
                    flow_id=self.parameters['flow_id'],
                    cluster_id=NS.tendrl_context.integration_id,
                )
            )
            raise AtomExecutionFailedError(
                "Invalid combination of pool update parameters. "
                "Pool name shoulnt be update with other parameters."
            )

        if 'Pool.pg_num' in self.parameters:
            fetched_pool = Pool(
                pool_id=self.parameters['Pool.pool_id']
            ).load()
            if self.parameters['Pool.pg_num'] <= fetched_pool.pg_num:
                Event(
                    Message(
                        priority="info",
                        publisher=NS.publisher_id,
                        payload={
                            "message": "New pg-num cannot be less than "
                            "existing value"
                        },
                        job_id=self.parameters['job_id'],
                        flow_id=self.parameters['flow_id'],
                        cluster_id=NS.tendrl_context.integration_id,
                    )
                )
                raise AtomExecutionFailedError(
                    "New pg-num cannot be less than existing value"
                )

        return True
