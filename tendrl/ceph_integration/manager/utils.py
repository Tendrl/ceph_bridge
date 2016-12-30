import logging
import os
import os.path
import subprocess

LOG = logging.getLogger(__name__)
FSID = "/etc/tendrl/ceph_integration/fsid"
TENDRL_CONTEXT = "/var/lib/tendrl/ceph_cluster_id"
NODE_CONTEXT = "/etc/tendrl/node_agent/node_context"


def get_tendrl_context():
    if os.path.isfile(TENDRL_CONTEXT):
        with open(TENDRL_CONTEXT) as f:
            cluster_id = f.read()
            LOG.info("Tendrl_context.cluster_id=%s found!" % cluster_id)
            return cluster_id
    else:
        return None


def get_node_context():
    if os.path.isfile(NODE_CONTEXT):
        with open(NODE_CONTEXT) as f:
            node_id = f.read()
            LOG.info("Node_context.node_id==%s found!" % node_id)
            return node_id


def get_fsid():
    # check if valid uuid is already present in node_context
    # if not present generate one and update the file
    if os.path.isfile(FSID):
        with open(FSID) as f:
            fsid = f.read()
            if fsid:
                LOG.info("Tendrl_context.fsid==%s found!" % fsid)
                return fsid
    else:
        return None


def set_fsid(fsid):
    current_fsid = get_fsid()
    if current_fsid is None:
        with open(FSID, 'wb+') as f:
            f.write(fsid)
            current_fsid = fsid
            LOG.info("Tendrl_context.fsid==%s created!" % fsid)

    return current_fsid


def get_sds_version():
    res = subprocess.check_output(['ceph', '--version'])
    return res.split()[2].split("-")[0]
