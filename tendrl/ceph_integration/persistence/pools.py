from tendrl.common.etcdobj.etcdobj import EtcdObj
from tendrl.common.etcdobj import fields


class Pool(EtcdObj):
    """A table for storing a FIFO of ClusterMonitor 'sync objects', i.e.

    cluster maps.

    """
    __name__ = 'clusters/%s/Pools/%s'

    updated = fields.StrField("updated")
    cluster_id = fields.StrField("cluster_id")
    pool_id = fields.StrField("pool_id")
    poolname = fields.StrField("poolname")
    pg_num = fields.StrField("pg_num")
    min_size = fields.StrField("min_size")

    def render(self):
        self.__name__ = self.__name__ % (self.cluster_id, self.pool_id)
        return super(Pool, self).render()
