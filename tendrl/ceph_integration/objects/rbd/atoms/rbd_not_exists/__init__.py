from tendrl.ceph_integration.objects.rbd import Rbd
from tendrl.commons.event import Event
from tendrl.commons.message import Message
from tendrl.commons import objects


class RbdNotExists(objects.BaseAtom):

    def __init__(self, *args, **kwargs):
        super(RbdNotExists, self).__init__(*args, **kwargs)

    def run(self):
        if self.parameters.get('Rbd.pool_id') is not None:
            Event(
                Message(
                    priority="info",
                    publisher=NS.publisher_id,
                    payload={
                        "message": "Checking if rbd: %s doesnt exist for pool"
                                   " %s" % (self.parameters['Rbd.name'],
                                            self.parameters['Rbd.pool_id'])
                    },
                    job_id=self.parameters['job_id'],
                    flow_id=self.parameters['flow_id'],
                    cluster_id=NS.tendrl_context.integration_id,
                )
            )
            rbd = Rbd(pool_id=self.parameters['Rbd.pool_id'],
                      name=self.parameters['Rbd.name'])
            if rbd.exists():
                Event(
                    Message(
                        priority="info",
                        publisher=NS.publisher_id,
                        payload={
                            "message": "Rbd: %s exists for pool %s" %
                                       (self.parameters['Rbd.name'],
                                        self.parameters['Rbd.pool_id'])
                        },
                        job_id=self.parameters['job_id'],
                        flow_id=self.parameters['flow_id'],
                        cluster_id=NS.tendrl_context.integration_id,
                    )
                )
                return False
            else:
                return True

        else:
            return True
