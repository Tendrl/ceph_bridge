from tendrl.ceph_integration import objects
from tendrl.ceph_integration.flows import CephIntegrationBaseFlow
from tendrl.ceph_integration.objects.rbd import Rbd


class ResizeRbd(CephIntegrationBaseFlow):
    obj = Rbd
    def __init__(self, *args, **kwargs):
        super(ResizeRbd, self).__init__(*args, **kwargs)

    def run(self):
        super(ResizeRbd, self).run()
