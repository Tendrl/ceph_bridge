from tendrl.commons.etcdobj import EtcdObj
from tendrl.commons import objects


class Rbd(objects.BaseObject):
    def __init__(self, name=None, size=None,
                 pool_id=None, flags=None, provisioned=None,
                 used=None, *args, **kwargs):
        super(Rbd, self).__init__(*args, **kwargs)

        self.value = 'clusters/%s/Pools/%s/Rbds/%s'
        self.name = name
        self.size = size
        self.pool_id = pool_id
        self.flags = flags
        self.provisioned = provisioned
        self.used = used
        self._etcd_cls = _Rbd


class _Rbd(EtcdObj):
    """A table of the Pool, lazily updated
    """
    __name__ = 'clusters/%s/Pools/%s/Rbds/%s'
    _tendrl_cls = Rbd

    def render(self):
        self.__name__ = self.__name__ %\
            (NS.tendrl_context.integration_id, self.pool_id, self.name)
        return super(_Rbd, self).render()
