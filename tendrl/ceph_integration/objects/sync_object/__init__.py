from tendrl.commons.etcdobj import EtcdObj
from tendrl.ceph_integration import objects


class SyncObject(objects.CephIntegrationBaseObject):
    def __init__(self, fsid=None, cluster_name=None,
                 sync_type=None, version=None, when=None,
                 data=None, updated=None, *args, **kwargs):
        super(SyncObject, self).__init__(*args, **kwargs)

        self.value = 'clusters/%s/maps/%s'
        self.fsid = fsid
        self.cluster_name = cluster_name
        self.sync_type = sync_type
        self.version = version
        self.when = when
        self.data = data
        self.updated = updated
        self._etcd_cls = _SyncObject


class _SyncObject(EtcdObj):
    """A table of the _Service, lazily updated
    """
    __name__ = 'clusters/%s/maps/%s'
    _tendrl_cls = SyncObject

    def render(self):
        self.__name__ = self.__name__ %\
            (tendrl_ns.tendrl_context.integration_id, self.sync_type)
        return super(_SyncObject, self).render()
