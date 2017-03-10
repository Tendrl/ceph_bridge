from tendrl.commons.etcdobj import EtcdObj
from tendrl.commons import objects


class Event(objects.BaseObject):
    def __init__(self, event_id=None, when=None,
                 severity=None, message=None, fsid=None,
                 fqdn=None, service_type=None, service_id=None,
                 *args, **kwargs):
        super(Event, self).__init__(*args, **kwargs)

        self.value = 'clusters/%s/events/%s'
        self.event_id = event_id
        self.when = when
        self.severity = severity
        self.message = message
        self.fsid = fsid
        self.fqdn = fqdn
        self.service_type = service_type
        self.service_id = service_id
        self._etcd_cls = _Event


class _Event(EtcdObj):
    """A table of the _Service, lazily updated
    """
    __name__ = 'clusters/%s/events/%s'
    _tendrl_cls = Event

    def render(self):
        self.__name__ = self.__name__ % (self.fsid, self.id)
        return super(_Event, self).render()
