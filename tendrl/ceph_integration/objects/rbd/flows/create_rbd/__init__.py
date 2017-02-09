from tendrl.ceph_integration import objects
from tendrl.ceph_integration.flows import CephIntegrationBaseFlow
from tendrl.ceph_integration.objects.pool import Pool


class CreateRbd(CephIntegrationBaseFlow):
    obj = Pool
    def __init__(self, *args, **kwargs):
        super(CreateRbd, self).__init__(*args, **kwargs)

    def run(self):
        super(CreateRbd, self).run()
