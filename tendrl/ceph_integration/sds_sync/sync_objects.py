import logging

import datetime

from tendrl.ceph_integration import ceph
from tendrl.ceph_integration.types import SYNC_OBJECT_TYPES
from tendrl.commons.utils.tz_utils import now

LOG = logging.getLogger(__name__)


class SyncObjects(object):
    """A collection of versioned objects, keyed by their class (which

    must be a SyncObject subclass).

    The objects are immutable, so it is safe to hand out references: new

    versions are new objects.

    """

    # Note that this *isn't* an enforced timeout on fetches, rather it is
    # the time after which we will start re-requesting maps on the assumption
    # that a previous fetch is MIA.
    FETCH_TIMEOUT = datetime.timedelta(seconds=10)

    def __init__(self, cluster_name):
        self._objects = dict([(t, t(None, None)) for t in SYNC_OBJECT_TYPES])
        self._cluster_name = cluster_name

        # When we issued a fetch() for this type, or None if no fetch
        # is underway
        self._fetching_at = dict([(t, None) for t in SYNC_OBJECT_TYPES])
        # The latest version we have heard about (not the latest we have
        # in our map)
        self._known_versions = dict([(t, None) for t in SYNC_OBJECT_TYPES])

    def set_map(self, typ, version, map_data):
        so = self._objects[typ] = typ(version, map_data)
        return so

    def get_version(self, typ):
        return self._objects[typ].version if self._objects[typ] else None

    def get_data(self, typ):
        return self._objects[typ].data if self._objects[typ] else None

    def get(self, typ):
        return self._objects[typ]

    def on_version(self, sync_type, new_version):
        """Notify me that a particular version of a particular map exists.

        I may choose to initiate RPC to retrieve the map

        """
        LOG.debug(
            "SyncObjects.on_version %s/%s" % (sync_type.str, new_version)
        )
        old_version = self.get_version(sync_type)
        if sync_type.cmp(new_version, old_version) > 0:
            known_version = self._known_versions[sync_type]
            if sync_type.cmp(new_version, known_version) > 0:
                # We are out of date: request an up to date copy
                LOG.info("Advanced known version %s/%s %s->%s" % (
                    self._cluster_name, sync_type.str, known_version,
                    new_version))
                self._known_versions[sync_type] = new_version
            else:
                LOG.info(
                    "on_version: %s is newer than %s" % (
                        new_version, old_version
                    )
                )

            # If we already have a request out for this type of map,
            # then consider cancelling it if we've already waited for
            # a while.
            if self._fetching_at[sync_type] is not None:
                if now() - self._fetching_at[sync_type] < self.FETCH_TIMEOUT:
                    LOG.info("Fetch already underway for %s" % sync_type.str)
                    return
                else:
                    LOG.warn("Abandoning fetch for %s started at %s" % (
                        sync_type.str, self._fetching_at[sync_type]))

            LOG.info(
                "on_version: fetching %s/%s , "
                "currently got %s, know %s" % (
                    sync_type, new_version, old_version, known_version
                )
            )
            return self.fetch(sync_type)

    def fetch(self, sync_type):
        LOG.debug("SyncObjects.fetch: %s" % sync_type)

        self._fetching_at[sync_type] = now()
        # TODO(Rohan) clean up unused 'since' argument
        return ceph.get_cluster_object(self._cluster_name,
                                       sync_type.str)

    def on_fetch_complete(self, sync_type, version, data):
        """:return A SyncObject if this version was new to us, else None

        """
        LOG.debug(
            "SyncObjects.on_fetch_complete %s/%s" % (
                sync_type.str, version)
        )
        self._fetching_at[sync_type] = None

        # A fetch might give us a newer version than we knew we had asked for
        if sync_type.cmp(version, self._known_versions[sync_type]) > 0:
            self._known_versions[sync_type] = version

        # Don't store this if we already got something newer
        if sync_type.cmp(version, self.get_version(sync_type)) <= 0:
            LOG.warn(
                "Ignoring outdated"
                " update %s/%s" % (sync_type.str, version)
            )
            new_object = None
        else:
            LOG.info("Got new version %s/%s" % (sync_type.str, version))
            new_object = self.set_map(sync_type, version, data)

        return new_object

