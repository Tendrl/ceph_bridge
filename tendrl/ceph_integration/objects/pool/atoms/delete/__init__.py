from tendrl.ceph_integration.manager.crud import Crud
from tendrl.ceph_integration import objects
from tendrl.ceph_integration.objects.pool import Pool


class Delete(objects.CephIntegrationBaseAtom):
    obj = Pool
    def __init__(self, *args, **kwargs):
        super(Delete, self).__init__(*args, **kwargs)

    def run(self):
        pool_id = self.parameters['Pool.pool_id']
        crud = Crud()
        crud.delete(
            "pool",
            pool_id
        )

        tendrl_ns.ceph_integration.objects.Pool(
            pool_id=pool_id,
            deleted="True"
        ).save()

        return True
