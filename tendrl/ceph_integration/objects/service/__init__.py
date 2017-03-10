from tendrl.commons.etcdobj import EtcdObj
from tendrl.commons import objects


class Service(objects.BaseObject):
    def __init__(self, fsid=None, service_type=None,
                 service_id=None, running=None, status=None,
                 server_uuid=None, server_fqdn=None, *args, **kwargs):
        super(Service, self).__init__(*args, **kwargs)

        self.value = 'clusters/ceph/%s/services/%s/%s/%s'
        self.fsid = fsid
        self.service_type = service_type
        self.service_id = service_id
        self.running = running
        self.status = status
        self.server_uuid = server_uuid
        self.server_fqdn = server_fqdn
        self._etcd_cls = _Service


class _Service(EtcdObj):
    """A table of the _Service, lazily updated
    """
    __name__ = 'clusters/ceph/%s/services/%s/%s/%s'
    _tendrl_cls = Service

    def render(self):
        self.__name__ = self.__name__ % (
            self.fsid, self.server_fqdn, self.service_type, self.service_id)
        return super(_Service, self).render()
