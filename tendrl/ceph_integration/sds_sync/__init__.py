import copy
import datetime
import etcd
import json
import os
import socket

import gevent.event
from pytz import utc


from tendrl.ceph_integration import ceph
from tendrl.ceph_integration.manager.crud import Crud
from tendrl.ceph_integration.manager.crush_node_request_factory import \
    CrushNodeRequestFactory
from tendrl.ceph_integration.manager.crush_request_factory import \
    CrushRequestFactory
from tendrl.ceph_integration.manager.ec_profile_request_factory import \
    ECProfileRequestFactory
from tendrl.ceph_integration.manager.osd_request_factory import \
    OsdRequestFactory
from tendrl.ceph_integration.manager.pool_request_factory import \
    PoolRequestFactory
from tendrl.ceph_integration.manager.rbd_request_factory import \
    RbdRequestFactory
from tendrl.ceph_integration.manager.request_collection import \
    RequestCollection
from tendrl.ceph_integration.sds_sync.sync_objects import SyncObjects

from tendrl.ceph_integration.types import CRUSH_MAP
from tendrl.ceph_integration.types import CRUSH_NODE
from tendrl.ceph_integration.types import EC_PROFILE
from tendrl.ceph_integration.types import ERROR
from tendrl.ceph_integration.types import INFO
from tendrl.ceph_integration.types import OSD
from tendrl.ceph_integration.types import POOL
from tendrl.ceph_integration.types import RBD
from tendrl.ceph_integration.types import SEVERITIES
from tendrl.ceph_integration.types import SYNC_OBJECT_STR_TYPE
from tendrl.ceph_integration.types import SYNC_OBJECT_TYPES
from tendrl.ceph_integration.types import WARNING

from tendrl.commons.event import Event
from tendrl.commons.message import ExceptionMessage
from tendrl.commons.message import Message
from tendrl.commons import sds_sync
from tendrl.commons.utils import cmd_utils
from tendrl.commons.utils.time_utils import now


class CephIntegrationSdsSyncStateThread(sds_sync.SdsSyncThread):
    def __init__(self):
        super(CephIntegrationSdsSyncStateThread, self).__init__()
        self._ping_cluster()
        self.update_time = datetime.datetime.utcnow().replace(tzinfo=utc)
        self._request_factories = {
            CRUSH_MAP: CrushRequestFactory,
            CRUSH_NODE: CrushNodeRequestFactory,
            OSD: OsdRequestFactory,
            POOL: PoolRequestFactory,
            RBD: RbdRequestFactory,
            EC_PROFILE: ECProfileRequestFactory
        }
        self._sync_objects = SyncObjects(self.name)
        self._request_coll = RequestCollection()

    def _ping_cluster(self):
        NS.tendrl_context = NS.tendrl_context.load()
        NS.node_context = NS.node_context.load()
        if NS.tendrl_context.cluster_id:
                cluster_data = ceph.heartbeat(NS.tendrl_context.cluster_id)
                NS.tendrl_context.cluster_id = self.fsid = cluster_data['fsid']
        else:
            cluster_data = ceph.heartbeat()
            if cluster_data:
                if "fsid" in cluster_data:
                    NS.tendrl_context.cluster_id = self.fsid = \
                        cluster_data['fsid']

        NS.tendrl_context.cluster_name = self.name = cluster_data['name']
        NS.tendrl_context.save()

    def _run(self):
        Event(
            Message(
                priority="info",
                publisher=NS.publisher_id,
                payload={"message": "%s running" % self.__class__.__name__}
            )
        )

        # Check if monitor key exists, if not sync
        try:
            NS._int.client.read(
                "clusters/%s/_mon_key" % NS.tendrl_context.integration_id
            )
        except etcd.EtcdKeyNotFound:
            out, err, rc = cmd_utils.Command(
                "ceph auth get mon. --cluster %s" %
                NS.tendrl_context.cluster_name
            ).run()

            if rc != 0:
                Event(
                    Message(
                        priority="debug",
                        publisher=NS.publisher_id,
                        payload={
                            "message": "Couldn't get monitor key. Error:%s" %
                            err
                        }
                    )
                )
            else:
                if out and out != "":
                    mon_sec = out.split('\n')[1].strip().split(
                        ' = ')[1].strip()
                    NS._int.wclient.write(
                        "clusters/%s/_mon_key" %
                        NS.tendrl_context.integration_id,
                        mon_sec
                    )

        while not self._complete.is_set():
            gevent.sleep(
                int(NS.config.data.get("sync_interval", 10))
            )
            cluster_data = ceph.heartbeat(NS.tendrl_context.cluster_id)

            self.on_heartbeat(cluster_data)

        Event(
            Message(
                priority="info",
                publisher=NS.publisher_id,
                payload={"message": "%s complete" % self.__class__.__name__}
            )
        )

    def on_heartbeat(self, cluster_data):
        """Handle a ceph.heartbeat.

        These tell us whether there are any new versions of

        cluster maps for us to fetch.

        """
        if cluster_data is None:
            return
        if cluster_data['versions'] is None:
            return
        self.update_time = datetime.datetime.utcnow().replace(tzinfo=utc)

        Event(
            Message(
                priority="info",
                publisher=NS.publisher_id,
                payload={"message": 'Checking for version increments in '
                                    'heartbeat...'
                         }
            )
        )
        for sync_type in SYNC_OBJECT_TYPES:
            data = self._sync_objects.on_version(
                sync_type, cluster_data['versions'][sync_type.str]
            )
            if data:
                self.on_sync_object(data)

        # Sync the utilization details for the cluster
        self._sync_utilization()

        # Get and update rbds for pools
        self._sync_rbds()

        # Get and update ec profiles for the cluster
        self._sync_ec_profiles()

        # Sync the OSD utilization details
        self._sync_osd_utilization()

    def _sync_osd_utilization(self):
        from ceph_argparse import json_command
        import rados
        _conf_file = os.path.join(
            "/etc/ceph",
            NS.tendrl_context.cluster_name + ".conf"
        )
        cluster_handle = rados.Rados(
            name=ceph.RADOS_NAME,
            clustername=NS.tendrl_context.cluster_name,
            conffile=_conf_file
        )
        cluster_handle.connect()
        prefix = 'osd df'
        out = ceph.rados_command(
            cluster_handle,
            prefix=prefix,
            args={}
        )
        if out:
            for entry in out['nodes']:
                fetched_osd = NS.ceph.objects.Osd(id=entry['id']).load()
                fetched_osd.total = entry['kb'] * 1024
                fetched_osd.used = entry['kb_used'] * 1024
                fetched_osd.used_pcnt = str(entry['utilization'])
                fetched_osd.save()
        cluster_handle.shutdown()

    def _sync_utilization(self):
        util_data = self._get_utilization_data()
        NS.ceph.objects.Utilization(
            total=util_data['cluster']['total'],
            used=util_data['cluster']['used'],
            available=util_data['cluster']['available'],
            pcnt_used=util_data['cluster']['pcnt_used']
        ).save()

        # Loop through the pools and update the utilization details
        try:
            pools = NS._int.client.read(
                "clusters/%s/Pools" % NS.tendrl_context.integration_id,
            )
        except etcd.EtcdKeyNotFound:
            # No pools so no need to continue with pool utilization sync
            return

        for entry in pools.leaves:
            fetched_pool = NS.ceph.objects.Pool(
                pool_id=entry.key.split("Pools/")[-1]
            ).load()
            pool_util_data = util_data['pools'].get(
                fetched_pool.pool_name,
                {}
            )
            fetched_pool.used = pool_util_data.get(
                'used',
                fetched_pool.used
            )
            fetched_pool.percent_used = pool_util_data.get(
                'pcnt_used',
                fetched_pool.percent_used
            )
            fetched_pool.save()

    def _sync_rbds(self):
        try:
            pools = NS._int.client.read(
                "clusters/%s/Pools" % NS.tendrl_context.integration_id,
                recursive=True
            )
            for child in pools._children:
                pool_id = child['key'].split('/')[-1]
                pool_name = NS._int.client.read(
                    "clusters/%s/Pools/%s/pool_name" %
                    (NS.tendrl_context.integration_id, pool_id)
                ).value
                rbd_details = self._get_rbds(pool_name)
                # Rbd out of band delete handling
                try:
                    rbds = NS._int.client.read(
                        "clusters/%s/Pools/%s/Rbds" %
                        (NS.tendrl_context.integration_id, pool_id)
                    )
                    old_rbds = []
                    for rbd in rbds.leaves:
                        old_rbds.append(rbd.key.split("/")[-1])
                    new_rbds = []
                    for k, v in rbd_details.iteritems():
                        new_rbds.append(k)
                    delete_rbds = set(old_rbds) - set(new_rbds)
                    for id in delete_rbds:
                        NS._int.client.delete(
                            "clusters/%s/Pools/%s/Rbds/%s" %
                            (NS.tendrl_context.integration_id, pool_id, id),
                            recursive=True
                        )
                except etcd.EtcdKeyNotFound as ex:
                    Event(
                        ExceptionMessage(
                            priority="debug",
                            publisher=NS.publisher_id,
                            payload={"message":
                                     "No rbds found for ceph cluster %s"
                                     % NS.tendrl_context.integration_id,
                                     "exception": ex
                                     }
                        )
                    )
                for k, v in rbd_details.iteritems():
                    NS.ceph.objects.Rbd(
                        name=k,
                        size=v['size'],
                        pool_id=pool_id,
                        flags=v['flags'],
                        provisioned=self._to_bytes(v['provisioned']) if v.get(
                            "provisioned") else None,
                        used=self._to_bytes(v['used'])
                    ).save()
                try:
                    rbds = NS._int.client.read(
                        "clusters/%s/Pools/%s/Rbds" %
                        (NS.tendrl_context.integration_id, pool_id)
                    )
                except etcd.EtcdKeyNotFound:
                    # no rbds for pool, continue
                    continue

                for entry in rbds.leaves:
                    fetched_rbd = NS.ceph.objects.Rbd(
                        pool_id=pool_id,
                        name=entry.key.split("Rbds/")[-1]
                    ).load()
                    if fetched_rbd.name not in rbd_details.keys():
                        NS._int.client.delete(
                            "clusters/%s/Pools/%s/Rbds/%s" % (
                                NS.tendrl_context.integration_id,
                                pool_id,
                                fetched_rbd.name
                            ),
                            recursive=True
                        )
        except etcd.EtcdKeyNotFound:
            pass

    def _sync_ec_profiles(self):
        """Invokes the below CLI commands

        1.
        ```ceph osd erasure-code-profile ls```

        and required output format is a list of ec profiles separated with new
        lines as below

        ```
           default
           k4m2
        ```
        2.
        ```ceph osd erasure-code-profile get {name}```

        and the required output format is '=' separated values in multiple
        lines

        ```
           k=2
           m=1
           plugin=jerasure
           directory={dir}
        ```

        """
        required_ec_profiles = [
            (2, 1),
            (4, 2),
            (6, 3),
            (8, 4)
        ]
        ec_profile_details = {}

        commands = [
            'osd', 'erasure-code-profile', 'ls'
        ]
        cmd_out = ceph.ceph_command(NS.tendrl_context.cluster_name, commands)
        if cmd_out['err'] == "":
            ec_profile_list = []
            for item in cmd_out['out'].split('\n'):
                if item != "":
                    ec_profile_list.append(item)

            for ec_profile in ec_profile_list:
                commands = [
                    'osd', 'erasure-code-profile', 'get', ec_profile
                ]
                cmd_out = ceph.ceph_command(
                    NS.tendrl_context.cluster_name,
                    commands
                )
                if cmd_out['err'] == "":
                    info = {}
                    for item in cmd_out['out'].split('\n'):
                        if item != "":
                            info[item.split('=')[0]] = \
                                item.split('=')[1].strip()
                            ec_profile_details[ec_profile] = info
        # Ec profile out of band delete handling
            try:
                ec_profiles = NS._int.client.read(
                    "clusters/%s/ECProfiles" %
                    (NS.tendrl_context.integration_id)
                )
                old_ec_profiles = []
                for ec_profile in ec_profiles.leaves:
                    old_ec_profiles.append(ec_profile.key.split("/")[-1])
                new_ec_profiles = []
                for k, v in ec_profile_details.iteritems():
                    new_ec_profiles.append(k)
                delete_ec_profiles = set(
                    old_ec_profiles) - set(new_ec_profiles)
                for id in delete_ec_profiles:
                    NS._int.client.delete(
                        "clusters/%s/ECProfiles/%s" %
                        (NS.tendrl_context.integration_id, id),
                        recursive=True
                    )
            except etcd.EtcdKeyNotFound as ex:
                Event(
                    ExceptionMessage(
                        priority="debug",
                        publisher=NS.publisher_id,
                        payload={"message": "key not found in etcd",
                                 "exception": ex
                                 }
                    )
                )
        available_ec_profiles = []
        for k, v in ec_profile_details.iteritems():
            NS.ceph.objects.ECProfile(
                name=k,
                k=v['k'],
                m=v['m'],
                plugin=v.get('plugin'),
                directory=v.get('directory'),
                ruleset_failure_domain=v.get('ruleset_failure_domain')
            ).save()
            available_ec_profiles.append((int(v['k']), int(v['m'])))

        # Create the missing ec_profile_details
        missing_ec_profiles = [
            item for item in required_ec_profiles
            if item not in available_ec_profiles
        ]
        for item in missing_ec_profiles:
            attrs = dict(
                name="k%sm%s" % (item[0], item[1]),
                k=item[0],
                m=item[1],
                plugin='jerasure',
                directory='/usr/lib/ceph/erasure-code'
            )
            crud = Crud()
            crud.create("ec_profile", attrs)

    def _emit_event(self, severity, resource, curr_value, msg,
                    plugin_instance=None):
        if not NS.node_context.node_id:
            return

        alert = {}
        alert['source'] = NS.publisher_id
        alert['pid'] = os.getpid()
        alert['time_stamp'] = now().isoformat()
        alert['alert_type'] = 'status'
        alert['severity'] = SEVERITIES[severity]
        alert['resource'] = resource
        alert['current_value'] = curr_value
        alert['tags'] = dict(
            message=msg,
            cluster_id=NS.tendrl_context.integration_id,
            cluster_name=NS.tendrl_context.cluster_name,
            sds_name=NS.tendrl_context.sds_name,
            fqdn=socket.getfqdn()
        )
        if plugin_instance:
            alert['tags']['plugin_instance'] = plugin_instance
        alert['node_id'] = NS.node_context.node_id
        Event(
            Message(
                "notice",
                "alerting",
                {'message': json.dumps(alert)}
            )
        )

    def _on_health(self, data):
        old_status = NS.ceph.objects.GlobalDetails().load().status
        new_status = data['overall_status']
        health_severity = {
            "HEALTH_OK": INFO,
            "HEALTH_WARN": WARNING,
            "HEALTH_ERR": ERROR
        }

        if old_status != new_status:
            if health_severity[new_status] < health_severity[old_status]:
                # A worsening of health
                event_sev = health_severity[new_status]
                msg = "Health of cluster '{name}' degraded from \
                    {old} to {new}".format(
                    old=old_status,
                    new=new_status,
                    name=NS.tendrl_context.cluster_name
                )
            else:
                # An improvement in health
                event_sev = INFO
                msg = "Health of cluster '{name}' recovered from \
                    {old} to {new}".format(
                    old=old_status,
                    new=new_status,
                    name=NS.tendrl_context.cluster_name
                )

            if health_severity[new_status] < INFO:
                pass

            self._emit_event(
                event_sev,
                'health',
                new_status,
                msg,
                plugin_instance=NS.tendrl_context.cluster_name
            )

    def _on_mon_status(self, data):
        old_quorum = NS.ceph.objects.SyncObject(
            sync_type='mon_status'
        ).load().data['quorum']
        new_quorum = set(data['quorum'])

        def _mon_event(severity, msg, mon_rank):
            name = data.mons_by_rank[mon_rank]['name']
            self._emit_event(
                severity,
                'monitor',
                str(new_quorum),
                msg.format(
                    cluster_name=NS.tendrl_context.cluster_name,
                    mon_name=name
                ),
                plugin_instance="mon.%s" % name
            )

        for rank in new_quorum - old_quorum:
            _mon_event(
                INFO,
                "Mon '{cluster_name}.{mon_name}' joined quorum",
                rank
            )

        for rank in old_quorum - new_quorum:
            _mon_event(
                WARNING,
                "Mon '{cluster_name}.{mon_name}' left quorum",
                rank
            )

    def _on_osd_map(self, data):
        if NS.ceph.objects.SyncObject(sync_type='osd_map').exists():
            old_osds_det = NS.ceph.objects.SyncObject(
                sync_type='osd_map'
            ).load().data['osds']
            old_osd_ids = set([o['osd'] for o in old_osds_det])
            new_osd_ids = set([o['osd'] for o in data['osds']])
            deleted_osds = old_osd_ids - new_osd_ids
            created_osds = new_osd_ids - old_osd_ids

            def osd_event(severity, msg, osd_id, curr_value):
                self._emit_event(
                    severity,
                    'osd_status',
                    curr_value,
                    msg.format(
                        name=NS.tendrl_context.cluster_name,
                        id=osd_id
                    ),
                    plugin_instance="osd.%s" % osd_id
                )

            # Generate events for removed OSDs
            for osd_id in deleted_osds:
                osd_event(
                    INFO,
                    "OSD {name}.{id} removed from the cluster map",
                    osd_id,
                    ""
                )

            # Generate events for added OSDs
            for osd_id in created_osds:
                osd_event(
                    INFO,
                    "OSD {name}.{id} added to the cluster map",
                    osd_id,
                    ""
                )

            # Generate events for changed OSDs
            for osd_id in old_osd_ids & new_osd_ids:
                old_osd = next(
                    (osd for osd in old_osds_det if osd['osd'] == osd_id),
                    None
                )
                new_osd = next(
                    (osd for osd in data['osds'] if osd['osd'] == osd_id),
                    None
                )
                if old_osd['up'] != new_osd['up']:
                    if bool(new_osd['up']):
                        osd_event(
                            INFO,
                            "OSD {name}.{id} came up",
                            osd_id,
                            str(new_osd['up'])
                        )
                    else:
                        osd_event(
                            WARNING,
                            "OSD {name}.{id} went down",
                            osd_id,
                            str(new_osd['up'])
                        )
                if old_osd['in'] != new_osd['in']:
                    if bool(new_osd['in']):
                        osd_event(
                            INFO,
                            "OSD {name}.{id} is in",
                            osd_id,
                            str(new_osd['in'])
                        )
                    else:
                        osd_event(
                            WARNING,
                            "OSD {name}.{id} went out",
                            osd_id,
                            str(new_osd['in'])
                        )

    def _on_pool_status(self, data):
        old_pools_det = NS.ceph.objects.SyncObject(
            sync_type='osd_map'
        ).load().data['pools']
        old_pool_ids = set([o['pool'] for o in old_pools_det])
        new_pool_ids = set([o['pool'] for o in data['pools']])
        deleted_pools = old_pool_ids - new_pool_ids
        created_pools = new_pool_ids - old_pool_ids

        def pool_event(severity, msg, pool_id):
            self._emit_event(
                severity,
                'pool',
                str(new_pool_ids),
                msg.format(
                    name=NS.tendrl_context.cluster_name,
                    id=pool_id
                ),
                plugin_instance="pool.%s" % pool_id
            )

        # Generate events for removed pools
        for pool_id in deleted_pools:
            pool_event(
                INFO,
                "pool {name}.{id} removed from cluster {name}",
                pool_id
            )

        # Generate events for added pools
        for pool_id in created_pools:
            pool_event(
                INFO,
                "pool {name}.{id} added to cluster {name}",
                pool_id
            )

    def on_sync_object(self, data):

        assert data['fsid'] == self.fsid

        sync_object = copy.deepcopy(data['data'])

        sync_type = SYNC_OBJECT_STR_TYPE[data['type']]
        new_object = self.inject_sync_object(
            data['type'], data['version'], sync_object
        )
        self._request_coll.on_map(sync_type, new_object)
        if new_object:
            # Check and raise any alerts if required

            # TODO(team) Enabled the below if condition as when
            # alerting needed for cluster health, mon status, pool
            # status etc

            # if sync_type.str == "health":
            #    self._on_health(sync_object)
            # if sync_type.str == "mon_status":
            #    self._on_mon_status(sync_object)
            if sync_type.str == "osd_map":
                # self._on_pool_status(sync_object)
                self._on_osd_map(sync_object)

            NS.ceph.objects.SyncObject(
                updated=now(), sync_type=sync_type.str,
                version=new_object.version if isinstance(new_object.version,
                                                         int) else None,
                when=now(), data=data['data']).save(update=False)

            if sync_type.str == "health":
                NS.ceph.objects.GlobalDetails(
                    status=sync_object['overall_status']
                ).save()
            if sync_type.str == "osd_map":
                # Pool out of band deletion handling
                try:
                    pools = NS._int.client.read(
                        "clusters/%s/Pools" % NS.tendrl_context.integration_id
                    )
                    old_pool_ids = []
                    for pool in pools.leaves:
                        old_pool_ids.append(int(pool.key.split("/")[-1]))
                    new_pool_ids = []
                    for raw_pool in sync_object.get('pools', []):
                        new_pool_ids.append(raw_pool['pool'])
                    delete_pool_ids = set(old_pool_ids) - set(new_pool_ids)
                    for id in delete_pool_ids:
                        NS._int.client.delete(
                            "clusters/%s/Pools/%s" % (
                                NS.tendrl_context.integration_id,
                                id
                            ),
                            recursive=True
                        )
                except etcd.EtcdKeyNotFound as ex:
                    Event(
                        ExceptionMessage(
                            priority="debug",
                            publisher=NS.publisher_id,
                            payload={"message": "No pools found \
                                     for ceph cluster %s"
                                     % NS.tendrl_context.integration_id,
                                     "exception": ex
                                     }
                        )
                    )
                for raw_pool in sync_object.get('pools', []):
                    Event(
                        Message(
                            priority="info",
                            publisher=NS.publisher_id,
                            payload={"message": "Updating Pool %s"
                                                % raw_pool['pool_name']
                                     }
                        )
                    )
                    pool_type = 'replicated'
                    if 'erasure_code_profile' in raw_pool and \
                        raw_pool['erasure_code_profile'] != "":
                        pool_type = 'erasure_coded'
                    quota_enabled = False
                    if ('quota_max_objects' in raw_pool and
                        raw_pool['quota_max_objects'] > 0) or \
                        ('quota_max_bytes' in raw_pool and
                         raw_pool['quota_max_bytes'] > 0):
                        quota_enabled = True
                    NS.ceph.objects.Pool(
                        pool_id=raw_pool['pool'],
                        pool_name=raw_pool['pool_name'],
                        pg_num=raw_pool['pg_num'],
                        type=pool_type,
                        erasure_code_profile=raw_pool.get(
                            'erasure_code_profile'
                        ),
                        min_size=raw_pool['min_size'],
                        size=raw_pool.get('size', None),
                        quota_enabled=quota_enabled,
                        quota_max_objects=raw_pool['quota_max_objects'],
                        quota_max_bytes=raw_pool['quota_max_bytes'],
                    ).save()
                # Osd out of band deletion handling
                try:
                    osds = NS._int.client.read(
                        "clusters/%s/Osds" % NS.tendrl_context.integration_id
                    )
                    old_osds = []
                    for osd in osds.leaves:
                        old_osds.append(str(osd.key.split("/")[-1]))
                    new_osds = []
                    for raw_osd in sync_object.get('osds', []):
                        new_osds.append(raw_osd['uuid'])
                    delete_osds = set(old_osds) - set(new_osds)
                    for id in delete_osds:
                        NS._int.client.delete(
                            "clusters/%s/Osds/%s" % (
                                NS.tendrl_context.integration_id,
                                id
                            ),
                            recursive=True
                        )
                except etcd.EtcdKeyNotFound as ex:
                    Event(
                        ExceptionMessage(
                            priority="debug",
                            publisher=NS.publisher_id,
                            payload={"message": "key not found in etcd",
                                     "exception": ex
                                     }
                        )
                    )
                for raw_osd in sync_object.get('osds', []):
                    Event(
                        Message(
                            priority="info",
                            publisher=NS.publisher_id,
                            payload={
                                "message": "Updating OSD %s" % raw_osd['osd']
                            }
                        )
                    )
                    osd_host = socket.gethostbyaddr(
                        raw_osd['public_addr'].split(':')[0]
                    )[0]
                    NS.ceph.objects.Osd(
                        id=raw_osd['osd'],
                        uuid=raw_osd['uuid'],
                        hostname=osd_host,
                        public_addr=raw_osd['public_addr'],
                        cluster_addr=raw_osd['cluster_addr'],
                        heartbeat_front_addr=raw_osd['heartbeat_front_addr'],
                        heartbeat_back_addr=raw_osd['heartbeat_back_addr'],
                        down_at=raw_osd['down_at'],
                        up_from=raw_osd['up_from'],
                        lost_at=raw_osd['lost_at'],
                        osd_up=raw_osd['up'],
                        osd_in=raw_osd['in'],
                        up_thru=raw_osd['up_thru'],
                        weight=str(raw_osd['weight']),
                        primary_affinity=str(raw_osd['primary_affinity']),
                        state=raw_osd['state'],
                        last_clean_begin=raw_osd['last_clean_begin'],
                        last_clean_end=raw_osd['last_clean_end']
                    ).save()
        else:
            Event(
                Message(
                    priority="debug",
                    publisher=NS.publisher_id,
                    payload={"message": "ClusterMonitor.on_sync_object: "
                                        "stale object received for %s"
                                        % data['type']
                             }
                )
            )

    def _get_rbds(self, pool_name):
        """Invokes the below CLI commands

        1.
        ```rbd ls --pool {name}```

        and required output format is a list of rbds separated with new
        lines as below

        ```
           mmrbd1
           mmdrbd2
        ```

        2.
        ```rbd --image {image-name} --pool {pool-name} info```

        and the required output format is as below

        ```
        rbd image 'mmrbd1':
            size 1024 MB in 256
        order 22 (4096 kB objects)
        block_name_prefix: rbd_data.1e31238e1f29
        format: 2
        features: layering, exclusive-lock, object-map, fast-diff, deep-flatten
        flags:
        ```

        """
        rbd_details = {}

        commands = [
            "ls"
        ]
        cmd_out = ceph.rbd_command(
            NS.tendrl_context.cluster_name,
            commands,
            pool_name
        )
        if cmd_out['err'] == "":
            rbd_list = []
            for item in cmd_out['out'].split('\n'):
                if item != "":
                    rbd_list.append(item)
            for rbd in rbd_list:
                commands = [
                    "info", "--image", rbd
                ]
                cmd_out = ceph.rbd_command(
                    NS.tendrl_context.cluster_name,
                    commands,
                    pool_name
                )
                if cmd_out['err'] == "":
                    rbd_info = {}
                    for item in cmd_out['out'].split('\n')[1:]:
                        if item != "":
                            if ":" in item:
                                key = item.split(':')[0]
                                if '\t' in key:
                                    key = key[1:]
                                rbd_info[key] = item.split(':')[1].strip()
                            else:
                                key = item.split()[0]
                                if '\t' in key:
                                    key = key[1:]
                                rbd_info[key] = item.split()[1].strip()
                            rbd_details[rbd] = rbd_info

                commands = [
                    "du", "--image", rbd
                ]
                cmd_out = ceph.rbd_command(
                    NS.tendrl_context.cluster_name,
                    commands,
                    pool_name
                )
                if cmd_out['status'] == 0 and cmd_out['out'] != "":
                    rbd_details[rbd]['provisioned'] = \
                        cmd_out['out'].split('\n')[1].split()[1]
                    rbd_details[rbd]['used'] = \
                        cmd_out['out'].split('\n')[1].split()[2]

        return rbd_details

    def _get_utilization_data(self):
        from ceph_argparse import json_command
        import rados
        _conf_file = os.path.join("/etc/ceph",
                                  NS.tendrl_context.cluster_name + ".conf")
        # TODO(shtripat) use ceph.ceph_command instead of rados/json_command
        cluster_handle = rados.Rados(
            name=ceph.RADOS_NAME,
            clustername=NS.tendrl_context.cluster_name,
            conffile=_conf_file
        )
        cluster_handle.connect()
        prefix = 'df'
        ret, outbuf, outs = json_command(
            cluster_handle,
            prefix=prefix,
            argdict={},
            timeout=ceph.RADOS_TIMEOUT
        )
        if ret != 0:
            cluster_handle.shutdown()
            raise rados.Error(outs)
        else:
            outbuf = outbuf.replace('RAW USED', 'RAW_USED')
            outbuf = outbuf.replace('%RAW USED', '%RAW_USED')
            outbuf = outbuf.replace('MAX AVAIL', 'MAX_AVAIL')
            lines = outbuf.split('\n')
            index = 0
            cluster_stat = {}
            pool_stat = {}
            pool_stat_available = False
            cluster_handle.shutdown()

            while index < len(lines):
                line = lines[index]
                if line == "" or line == '\n':
                    index += 1
                    continue
                if "GLOBAL" in line:
                    index += 1
                    if len(lines) < 3:
                        raise rados.Error("Failed to parse pool stats data")
                    cluster_fields = lines[index].split()
                    cluster_size_idx = self._idx_in_list(
                        cluster_fields,
                        'SIZE'
                    )
                    cluster_avail_idx = self._idx_in_list(
                        cluster_fields,
                        'AVAIL'
                    )
                    cluster_used_idx = self._idx_in_list(
                        cluster_fields,
                        'RAW_USED'
                    )
                    cluster_pcnt_used_idx = self._idx_in_list(
                        cluster_fields,
                        '%RAW_USED'
                    )
                    if cluster_size_idx == -1 or cluster_avail_idx == -1 or \
                        cluster_used_idx == -1 or cluster_pcnt_used_idx == -1:
                        raise rados.Error("Missing fields in cluster stat")
                    index += 1
                    if index >= len(lines):
                        Event(
                            Message(
                                priority="debug",
                                publisher=NS.publisher_id,
                                payload={"message": "No cluster stats to parse"
                                         }
                            )
                        )
                        return {'cluster': cluster_stat, 'pools': {}}
                    line = lines[index]
                    cluster_fields = line.split()
                    if len(cluster_fields) < 4:
                        Event(
                            Message(
                                priority="debug",
                                publisher=NS.publisher_id,
                                payload={"message": "Missing fields in cluster"
                                                    " stat"
                                         }
                            )
                        )
                        return {'cluster': cluster_stat, 'pools': {}}
                    cluster_stat['total'] = self._to_bytes(
                        cluster_fields[cluster_size_idx]
                    )
                    cluster_stat['used'] = self._to_bytes(
                        cluster_fields[cluster_used_idx]
                    )
                    cluster_stat['available'] = self._to_bytes(
                        cluster_fields[cluster_avail_idx]
                    )
                    cluster_stat['pcnt_used'] = cluster_fields[
                        cluster_pcnt_used_idx
                    ]
                if "POOLS" in line:
                    pool_stat_available = True
                    index += 1
                    if index >= len(lines):
                        Event(
                            Message(
                                priority="debug",
                                publisher=NS.publisher_id,
                                payload={"message": "No pool stats to parse"}
                            )
                        )
                        return {'cluster': cluster_stat, 'pools': {}}
                    pool_fields = lines[index].split()
                    pool_name_idx = self._idx_in_list(pool_fields, 'NAME')
                    pool_id_idx = self._idx_in_list(pool_fields, 'ID')
                    pool_used_idx = self._idx_in_list(pool_fields, 'USED')
                    pool_pcnt_used_idx = self._idx_in_list(
                        pool_fields,
                        '%USED'
                    )
                    pool_max_avail_idx = self._idx_in_list(
                        pool_fields,
                        'MAX_AVAIL'
                    )
                    if pool_name_idx == -1 or pool_id_idx == -1 or \
                        pool_used_idx == -1 or pool_pcnt_used_idx == -1 or \
                        pool_max_avail_idx == -1:
                        Event(
                            Message(
                                priority="debug",
                                publisher=NS.publisher_id,
                                payload={"message": "Missing fields in pool "
                                                    "stat"
                                         }
                            )
                        )
                        return {'cluster': cluster_stat, 'pools': {}}
                    index += 1
                if pool_stat_available is True:
                    line = lines[index]
                    pool_fields = line.split()
                    if len(pool_fields) < 5:
                        Event(
                            Message(
                                priority="debug",
                                publisher=NS.publisher_id,
                                payload={"message": "Missing fields in pool"
                                                    " stat"
                                         }
                            )
                        )
                        return {'cluster': cluster_stat, 'pools': {}}

                    loc_dict = {}
                    loc_dict['available'] = self._to_bytes(
                        pool_fields[pool_max_avail_idx]
                    )
                    loc_dict['used'] = self._to_bytes(
                        pool_fields[pool_used_idx]
                    )
                    loc_dict['pcnt_used'] = pool_fields[pool_pcnt_used_idx]
                    pool_stat[pool_fields[pool_name_idx]] = loc_dict
                index += 1

            return {'cluster': cluster_stat, 'pools': pool_stat}

    def _idx_in_list(self, list, str):
        idx = -1
        for item in list:
            idx += 1
            if item == str:
                return idx
        return -1

    def _to_bytes(self, str):
        if str.endswith('K') or str.endswith('k'):
            return int(str[:-1]) * 1024
        if str.endswith('M') or str.endswith('m'):
            return int(str[:-1]) * 1024 * 1024
        if str.endswith('G') or str.endswith('g'):
            return int(str[:-1]) * 1024 * 1024 * 1024
        if str.endswith('T') or str.endswith('t'):
            return int(str[:-1]) * 1024 * 1024 * 1024 * 1024
        if str.endswith('P') or str.endswith('p'):
            return int(str[:-1]) * 1024 * 1024 * 1024 * 1024 * 1024
        return int(str)

    def inject_sync_object(self, sync_type, version, data):
        sync_type = SYNC_OBJECT_STR_TYPE[sync_type]
        new_object = self._sync_objects.on_fetch_complete(
            sync_type, version, data
        )

        return new_object

    def get_sync_object_data(self, object_type):
        """:param object_type: A SyncObject subclass

        :returns: a json-serializable object

        """
        return self._sync_objects.get_data(object_type)

    def get_sync_object(self, object_type):
        """:param object_type: A SyncObject subclass

        :returns: a SyncObject instance

        """
        return self._sync_objects.get(object_type)

    def _request(self, method, obj_type, *args, **kwargs):
        """Create and submit UserRequest for an apply, create, update or delete.

        """
        request_factory = self.get_request_factory(obj_type)

        request = getattr(request_factory, method)(*args, **kwargs)

        response = request.submit()

        # Check the result status and accordingly set the error state
        # sample responses:
        # 1. {'status': 1, 'err': 'rbd command timed out', 'out': ''}
        # 2. {'status': 0, 'err': '', 'out': ''}
        # 3. {'versions':{
        #       'osd_map': 17,
        #       'pg_summary': '1710d2db9cdf746e06ee392786f130aa',
        #       'mds_map': None,
        #       'mon_status': 8,
        #       'health': 'd9f0d31b4021c00d14bccee24891daca',
        #       'mon_map': 3,
        #       'config': 'fa52cae4e8f8d04f79969385432eb145'
        #       },
        #     'error_status': '',
        #     'results': [None, None, None],
        #     'fsid': '140cd3d5-58e4-4935-a954-d946ceff371d',
        #     'error': False
        #    }
        if ('status' in response) and response['status'] != 0:
            request.error = True
            request.error_message = response['err']
        elif ('error' in response) and response['error']:
            request.error = True
            request.error_message = response['error_status']

        request.complete_jid(response)
        self._request_coll._by_request_id[request.id] = request
        if request:
            return {
                'request': request,
                'response': response
            }
        else:
            return None

    def request_delete(self, obj_type, obj_id):
        return self._request('delete', obj_type, obj_id)

    def request_create(self, obj_type, attributes):
        return self._request('create', obj_type, attributes)

    def request_rbd_delete(self, pool_id, rbd_name):
        return self._request(
            "delete_rbd",
            "rbd",
            pool_id=pool_id,
            rbd_name=rbd_name
        )

    def request_update(self, command, obj_type, obj_id, attributes):
        return self._request(command, obj_type, obj_id, attributes)

    def request_apply(self, obj_type, obj_id, command):
        return self._request(command, obj_type, obj_id)

    def get_valid_commands(self, object_type, obj_ids):
        return self.get_request_factory(
            object_type).get_valid_commands(obj_ids)

    def get_request_factory(self, object_type):
        try:
            return self._request_factories[object_type]()
        except KeyError:
            raise ValueError(
                "{0} is not one of {1}".format(
                    object_type, self._request_factories.keys()
                )
            )
