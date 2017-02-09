from tendrl.ceph_integration.manager.crud import Crud
from tendrl.ceph_integration import objects
from tendrl.ceph_integration.objects.rbd import Rbd


class Create(objects.CephIntegrationBaseAtom):
    obj = Rbd
    def __init__(self, *args, **kwargs):
        super(Create, self).__init__(*args, **kwargs)

    def run(self):
        attrs = dict(name=self.parameters['Rbd.name'],
                     size=self.parameters['Rbd.size'],
                     pool_id=self.parameters.get('Rbd.pool_id')
                     )
        crud = Crud()
        crud.create("rbd", attrs)
        return True
