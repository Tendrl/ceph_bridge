import logging

from tendrl.ceph_integration.manager.request_factory import RequestFactory
from tendrl.ceph_integration.manager.user_request import RbdCreatingRequest
from tendrl.ceph_integration.manager.user_request import RbdMapModifyingRequest
from tendrl.ceph_integration.types import OsdMap


LOG = logging.getLogger(__name__)

# Valid values for the 'var' argument to 'ceph osd pool set'
POOL_PROPERTIES = ["size", "min_size", "crash_replay_interval",
                   "pg_num", "pgp_num", "crush_ruleset", "hashpspool"]

# In Ceph versions before mon_osd_max_split_count, assume it is set to this
LEGACY_MON_OSD_MAX_SPLIT_COUNT = "32"


class RbdRequestFactory(RequestFactory):

    def _resolve_pool(self, pool_id):
        osd_map = tendrl_ns.state_sync_thread.get_sync_object(OsdMap)
        return osd_map.pools_by_id[pool_id]

    def delete_rbd(self, pool_id=None, rbd_name=None):
        # Resolve pool ID to name
        pool_name = self._resolve_pool(pool_id)['pool_name']

        # TODO(Rohan) perhaps the REST API should have something in the body to
        # make it slightly harder to accidentally delete a pool, to respect
        # the severity of this operation since we're hiding the
        # --yes-i-really-really-want-to
        # stuff here
        # TODO(Rohan) handle errors in a way that caller can show to a user,
        # e.g.
        # if the name is wrong we should be sending a structured errors dict
        # that they can use to associate the complaint with the 'name' field.
        commands = [
            'rm', rbd_name
        ]
        return RbdMapModifyingRequest(
            "Deleting image '{name}'".format(name=rbd_name),
            self._cluster_monitor.fsid, self._cluster_monitor.name, pool_name,
            commands
        )

    def update(self, rbd_name, attributes):
        osd_map = tendrl_ns.state_sync_thread.get_sync_object(OsdMap)
        pool = self._resolve_pool(attributes['pool_id'])
        pool_name = pool['pool_name']

        if 'size' in attributes:
            commands = [
                'resize', '--image', rbd_name, '--size', attributes.get('size')
            ]
            return RbdMapModifyingRequest(
                "Modifying image '{name}' ({attrs})".format(
                    name=rbd_name, attrs=", ".join(
                        "%s=%s" % (k, v) for k, v in attributes.items())
                ),
                self._cluster_monitor.fsid,
                self._cluster_monitor.name,
                pool_name,
                commands
            )

    def create(self, attributes):
        osd_map = tendrl_ns.state_sync_thread.get_sync_object(OsdMap)
        pool = self._resolve_pool(attributes['pool_id'])
        pool_name = pool['pool_name']

        commands = [
            'create', attributes['name'], '--size', attributes['size']
        ]

        return RbdCreatingRequest(
            "Creating image '{name}'".format(name=attributes['name']),
            self._cluster_monitor.fsid, self._cluster_monitor.name,
            attributes['name'], pool_name, commands)
