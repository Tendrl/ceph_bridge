import etcd

from tendrl.ceph_integration import objects
from tendrl.ceph_integration.objects.pool import Pool
from tendrl.commons.event import Event
from tendrl.commons.message import Message


class NamedPoolNotExists(objects.CephIntegrationBaseAtom):
    obj = Pool
    def __init__(self, *args, **kwargs):
        super(NamedPoolNotExists, self).__init__(*args, **kwargs)

    def run(self):
        Event(
            Message(
                priority="info",
                publisher=tendrl_ns.publisher_id,
                payload={
                    "message": "Checking if pool with name %s doesnt exist" %
                    self.parameters['Pool.poolname']
                },
                request_id=self.parameters['request_id'],
                flow_id=self.parameters['flow_id'],
                cluster_id=tendrl_ns.tendrl_context.integration_id,
            )
        )

        try:
            pools = tendrl_ns.etcd_orm.client.read(
                "clusters/%s/Pools" % tendrl_ns.tendrl_context.integration_id
            )
        except etcd.EtcdKeyNotFound:
            # No pools available in cluster, return True
            return True

        for pool in pools._children:
            fetched_pool = Pool(
                pool_id=pool['key'].split('/')[-1]
            ).load()
            if fetched_pool.pool_name == \
                self.parameters['Pool.poolname']:
                Event(
                    Message(
                        priority="info",
                        publisher=tendrl_ns.publisher_id,
                        payload={
                            "message": "Pool with name %s already exists" %
                            self.parameters['Pool.poolname']
                        },
                        request_id=self.parameters['request_id'],
                        flow_id=self.parameters['flow_id'],
                        cluster_id=tendrl_ns.tendrl_context.integration_id,
                    )
                )
                return False

        return True
