from ruamel import yaml

import importlib
import os

from tendrl.commons import objects
from tendrl.commons import etcdobj
from tendrl.ceph_integration.objects.definition import ceph


# Definitions need there own special init and have to be present in the NS
# before anything else, Hence subclassing BaseObject


class Definition(objects.BaseObject):
    def __init__(self, *args, **kwargs):
        super(Definition, self).__init__(*args, **kwargs)

        self.value = 'clusters/%s/_NS/definitions'
        self.data = ceph.data
        self._parsed_defs = yaml.safe_load(self.data)
        self._etcd_cls = _DefinitionEtcd

    def get_parsed_defs(self):
        self._parsed_defs = yaml.safe_load(self.data)
        return self._parsed_defs

    def load_definition(self):
        return {}


class _DefinitionEtcd(etcdobj.EtcdObj):
    """A table of the Definitions, lazily updated
    """
    __name__ = 'clusters/%s/_NS/definitions'
    _tendrl_cls = Definition

    def render(self):
        self.__name__ = self.__name__ % NS.tendrl_context.integration_id
        return super(_DefinitionEtcd, self).render()
