from tendrl.commons.etcdobj import EtcdObj
from tendrl.commons import objects


class SyncObject(objects.BaseObject):
    def __init__(self, sync_type=None, version=None, when=None,
                 data=None, updated=None, *args, **kwargs):
        super(SyncObject, self).__init__(*args, **kwargs)

        self.value = 'clusters/%s/maps/%s'
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
            (NS.tendrl_context.integration_id, self.sync_type)
        return super(_SyncObject, self).render()
