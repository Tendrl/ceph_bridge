from tendrl.ceph_integration.manager.crud import Crud
from tendrl.ceph_integration.manager import utils as manager_utils
from tendrl.ceph_integration import objects


class Delete(objects.CephIntegrationBaseAtom):
    def __init__(self, config=None, *args, **kwargs):
        super(Create, self).__init__(*args, **kwargs)
        self.obj = objects.Pool

    def run(self, parameters):
        cluster_id = parameters['Tendrl_context.integration_id']
        pool_id = parameters['Pool.pool_id']
        fsid = manager_utils.get_fsid()
        crud = Crud(parameters['manager'])
        crud.delete(
            fsid,
            "pool",
            pool_id
        )

        etcd_client = parameters['etcd_client']
        pool_key = "clusters/%s/Pools/%s/deleted" % (cluster_id, pool_id)
        etcd_client.write(pool_key, "True")

        return True
