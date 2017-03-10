try:
    from gevent import monkey
except ImportError:
    pass
else:
    monkey.patch_all()

from tendrl.commons import TendrlNS


class CephIntegrationNS(TendrlNS):
    def __init__(
        self,
        ns_name='tendrl.ceph_integration',
        ns_src='tendrl.ceph_integration'
    ):
        super(CephIntegrationNS, self).__init__(ns_name, ns_src)
