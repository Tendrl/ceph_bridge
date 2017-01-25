from tendrl.commons.etcdobj import EtcdObj
from tendrl.ceph_integration import objects


class Pool(objects.CephIntegrationBaseObject):
    def __init__(self, pool_id=None,
                 poolname=None, pg_num=None, min_size=None,
                 used=None, percent_used=None, *args, **kwargs):
        super(Pool, self).__init__(*args, **kwargs)

        self.value = 'clusters/%s/Pools/%s'
        self.pool_id = pool_id
        self.poolname = poolname
        self.pg_num = pg_num
        self.min_size = min_size
        self.used = used
        self.percent_used = percent_used
        self._etcd_cls = _Pool


class _Pool(EtcdObj):
    """A table of the Pool, lazily updated
    """
    __name__ = 'clusters/%s/Pools/%s'
    _tendrl_cls = Pool

    def render(self):
        self.__name__ = self.__name__ %\
            (tendrl_ns.tendrl_context.integration_id, self.pool_id)
        return super(_Pool, self).render()
