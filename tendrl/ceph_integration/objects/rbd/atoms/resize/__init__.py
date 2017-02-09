from tendrl.ceph_integration.manager.crud import Crud
from tendrl.ceph_integration import objects
from tendrl.ceph_integration.objects.rbd import Rbd


class Resize(objects.CephIntegrationBaseAtom):
    obj = Rbd
    def __init__(self, *args, **kwargs):
        super(Resize, self).__init__(*args, **kwargs)

    def run(self):
        attrs = dict(pool_id=self.parameters['Rbd.pool_id'],
                     size=self.parameters['Rbd.size'])
        crud = Crud()
        crud.update("rbd", self.parameters['Rbd.name'], attrs)
        return True
