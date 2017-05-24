from tendrl.ceph_integration.objects.pool import Pool
from tendrl.commons.event import Event
from tendrl.commons.message import Message
from tendrl.commons import objects
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

        if 'Pool.pg_num' in self.parameters:
            fetched_pool = Pool(
                pool_id=self.parameters['Pool.pool_id']
            ).load()
            if self.parameters['Pool.pg_num'] <= int(fetched_pool.pg_num):
                Event(
                    Message(
                        priority="error",
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
