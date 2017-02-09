from tendrl.ceph_integration import objects
from tendrl.ceph_integration.flows import CephIntegrationBaseFlow
from tendrl.ceph_integration.objects.rbd import Rbd


class DeleteRbd(CephIntegrationBaseFlow):
    obj = Rbd
    def __init__(self, *args, **kwargs):
        super(DeleteRbd, self).__init__(*args, **kwargs)

    def run(self):
        super(DeleteRbd, self).run()
