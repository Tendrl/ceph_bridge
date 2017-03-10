from tendrl.commons.etcdobj import EtcdObj
from tendrl.commons import objects


class Utilization(objects.BaseObject):
    def __init__(self, total=None, used=None,
                 available=None, pcnt_used=None,
                 *args, **kwargs):
        super(Utilization, self).__init__(*args, **kwargs)

        self.value = 'clusters/%s/Utilization'
        self.total = total
        self.used = used
        self.available = available
        self.pcnt_used = pcnt_used
        self._etcd_cls = _Utilization


class _Utilization(EtcdObj):
    """A table of the Utilization, lazily updated
    """
    __name__ = 'clusters/%s/Utilization'
    _tendrl_cls = Utilization

    def render(self):
        self.__name__ = self.__name__ % NS.tendrl_context.integration_id
        return super(_Utilization, self).render()
