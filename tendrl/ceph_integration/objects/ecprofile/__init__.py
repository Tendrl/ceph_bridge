from tendrl.commons.etcdobj import EtcdObj
from tendrl.commons import objects


class ECProfile(objects.BaseObject):
    def __init__(self, name=None, k=None,
                 m=None, plugin=None,
                 directory=None,
                 ruleset_failure_domain=None,
                 *args, **kwargs):
        super(ECProfile, self).__init__(*args, **kwargs)

        self.value = 'clusters/%s/ECProfiles/%s'
        self.name = name
        # The no of data chunks
        self.k = k
        # The no of coding chunks
        # It means that `m` OSDs could be out without losing any data out of
        # total k+m
        self.m = m
        self.plugin = plugin
        self.directory = directory
        self.ruleset_failure_domain = ruleset_failure_domain
        self._etcd_cls = _ECProfile


class _ECProfile(EtcdObj):
    __name__ = 'clusters/%s/ECProfiles/%s'
    _tendrl_cls = ECProfile

    def render(self):
        self.__name__ = self.__name__ %\
            (NS.tendrl_context.integration_id, self.name)
        return super(_ECProfile, self).render()
