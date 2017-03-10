import json
import logging
import os
import subprocess

from tendrl.commons.etcdobj import EtcdObj
from tendrl.commons import objects

LOG = logging.getLogger(__name__)
DEFAULT_CEPH_CLUSTER_NAME = "ceph"


class TendrlContext(objects.BaseObject):
    def __init__(self, integration_id=None, fsid=None, *args, **kwargs):
        super(TendrlContext, self).__init__(*args, **kwargs)

        self.value = 'clusters/%s/TendrlContext'

        # integration_id is the Tendrl generated cluster UUID
        self.integration_id = integration_id or \
            self._get_local_integration_id()
        self.fsid = fsid or self._get_local_fsid()
        self.sds_name, self.sds_version = self._get_sds_details()
        self.integration_name = self._get_integration_name()
        self._etcd_cls = _TendrlContextEtcd

    def _get_integration_name(self):
        cluster_name = DEFAULT_CEPH_CLUSTER_NAME
        # TODO(team) This file is valid for CentOS and RHEL. Needs to
        # be handled while ubuntu support is needed.
        ceph_cfg_file = "/etc/sysconfig/ceph"
        if not os.path.exists(ceph_cfg_file):
            LOG.warning("config file: %s not found" % ceph_cfg_file)
            return cluster_name

        with open(ceph_cfg_file) as f:
            for line in f:
                if line.startswith("CLUSTER="):
                    cluster_name = line.split('\n')[0].split('=')[-1]
                    break
        return cluster_name

    def create_local_integration_id(self):
        tendrl_context_path = "/etc/tendrl/ceph-integration/integration_id"
        with open(tendrl_context_path, 'wb+') as f:
            f.write(self.integration_id)
            LOG.info("SET_LOCAL: "
                     "NS.ceph_integration.objects.TendrlContext"
                     ".integration_id==%s" %
                     self.integration_id)

    def _get_local_integration_id(self):
        try:
            tendrl_context_path = "/etc/tendrl/ceph-integration/integration_id"
            if os.path.isfile(tendrl_context_path):
                with open(tendrl_context_path) as f:
                    integration_id = f.read()
                    if integration_id:
                        LOG.info(
                            "GET_LOCAL: "
                            "NS.ceph_integration.objects.TendrlContext"
                            ".integration_id==%s" % integration_id)
                        return integration_id
        except AttributeError:
            return None

    def create_local_fsid(self):
        tendrl_context_path = "/etc/tendrl/ceph-integration/fsid"
        with open(tendrl_context_path, 'wb+') as f:
            f.write(self.fsid)
            LOG.info("SET_LOCAL: "
                     "NS.ceph_integration.objects.TendrlContext.fsid"
                     "==%s" %
                     self.fsid)

    def _get_local_fsid(self):
        try:
            tendrl_context_path = "/etc/tendrl/ceph-integration/fsid"
            if os.path.isfile(tendrl_context_path):
                with open(tendrl_context_path) as f:
                    fsid = f.read()
                    if fsid:
                        LOG.info(
                            "GET_LOCAL: "
                            "NS.ceph_integration.objects.TendrlContext"
                            ".fsid==%s" % fsid)
                        return fsid
        except AttributeError:
            return None

    def _get_sds_details(self):
        # Run the command `ceph --version` which works seamlessly on OSD nodes
        # as well, rather than running `ceph version -f json`. This command can
        # worok only on monitor nodes.
        cmd = subprocess.Popen(
            "ceph --version",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        out, err = cmd.communicate()
        if err and 'command not found' in err:
            LOG.info("ceph not installed on host")
            return None

        # The output format from the command `ceph --version` is
        # `ceph version 10.2.5 (c461ee19ecbc0c5c330aca20f7392c9a00730367)`
        # We just split the output on space and take the required values
        if out:
            details = out.split()

            version = details[2]
            name = details[0]
            return name, version


class _TendrlContextEtcd(EtcdObj):
    """A table of the tendrl context, lazily updated
    """
    __name__ = 'clusters/%s/TendrlContext'
    _tendrl_cls = TendrlContext

    def render(self):
        self.__name__ = self.__name__ % NS.tendrl_context.integration_id
        return super(_TendrlContextEtcd, self).render()
