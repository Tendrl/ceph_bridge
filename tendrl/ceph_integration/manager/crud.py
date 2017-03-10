import logging

from tendrl.ceph_integration.types import CRUSH_MAP
from tendrl.ceph_integration.types import CRUSH_NODE
from tendrl.ceph_integration.types import EC_PROFILE
from tendrl.ceph_integration.types import NotFound
from tendrl.ceph_integration.types import OSD
from tendrl.ceph_integration.types import OSD_MAP
from tendrl.ceph_integration.types import POOL
from tendrl.ceph_integration.types import RBD

LOG = logging.getLogger(__name__)


class Crud(object):

    def __init__(self):
        super(Crud, self).__init__()

    def update(self, object_type, object_id, attributes):
        """Modify an object in a cluster.

        """
        if object_type == OSD:
            return NS.state_sync_thread.request_update(
                'update',
                OSD,
                object_id,
                attributes
            )
        elif object_type == POOL:
            return NS.state_sync_thread.request_update(
                'update',
                POOL,
                object_id,
                attributes
            )
        elif object_type == OSD_MAP:
            return NS.state_sync_thread.request_update(
                'update_config', OSD, object_id, attributes
            )

        elif object_type == CRUSH_MAP:
            return NS.state_sync_thread.request_update(
                'update', CRUSH_MAP, object_id, attributes
            )

        elif object_type == CRUSH_NODE:
            return NS.state_sync_thread.request_update(
                'update', CRUSH_NODE, object_id, attributes
            )
        elif object_type == RBD:
            return NS.state_sync_thread.request_update(
                'update', RBD, object_id, attributes
            )
        else:
            raise NotImplementedError(object_type)

    def apply(self, object_type, object_id, command):
        """Apply commands that do not modify an object in a cluster.

        """

        if object_type == OSD:
            return NS.state_sync_thread.request_apply(
                OSD,
                object_id,
                command
            )
        else:
            raise NotImplementedError(object_type)

    def get_valid_commands(self, object_type, object_ids):
        """Determine what commands can be run on OSD object_ids

        """
        try:
            valid_commands = NS.state_sync_thread.get_valid_commands(
                object_type,
                object_ids
            )
        except KeyError as e:
            raise NotFound(object_type, str(e))

        return valid_commands

    def create(self, object_type, attributes):
        if object_type == POOL:
            return NS.state_sync_thread.request_create(POOL, attributes)
        elif object_type == CRUSH_NODE:
            return NS.state_sync_thread.request_create(
                CRUSH_NODE,
                attributes
            )
        elif object_type == RBD:
            return NS.state_sync_thread.request_create(
                RBD,
                attributes
            )
        elif object_type == EC_PROFILE:
            return NS.state_sync_thread.request_create(
                EC_PROFILE,
                attributes
            )
        else:
            raise NotImplementedError(object_type)

    def delete(self, object_type, object_id):
        if object_type == POOL:
            return NS.state_sync_thread.request_delete(
                POOL,
                object_id
            )
        elif object_type == CRUSH_NODE:
            return NS.state_sync_thread.request_delete(
                CRUSH_NODE,
                object_id
            )
        elif object_type == EC_PROFILE:
            return NS.state_sync_thread.request_delete(
                EC_PROFILE,
                object_id
            )
        else:
            raise NotImplementedError(object_type)
