from tendrl.ceph_integration import objects
from tendrl.ceph_integration.flows import CephIntegrationBaseFlow
from tendrl.ceph_integration.objects.pool import Pool


class UpdatePool(CephIntegrationBaseFlow):
    obj = Pool
    def __init__(self, *args, **kwargs):
        super(UpdatePool, self).__init__(*args, **kwargs)

    def run(self):
        super(UpdatePool, self).run()
