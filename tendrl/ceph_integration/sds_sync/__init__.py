import copy
import datetime

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
from tendrl.ceph_integration.types import OSD
from tendrl.ceph_integration.types import POOL
from tendrl.ceph_integration.types import RBD
from tendrl.ceph_integration.types import SYNC_OBJECT_STR_TYPE
from tendrl.ceph_integration.types import SYNC_OBJECT_TYPES
from tendrl.ceph_integration.util import now

from tendrl.commons.event import Event
from tendrl.commons.message import Message
from tendrl.commons import sds_sync


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

        while not self._complete.is_set():
            gevent.sleep(10)
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

        # Get and update rbds for pools
        self._sync_rbds()

        # Get and update ec profiles for the cluster
        self._sync_ec_profiles()

    def _sync_rbds(self):
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

    def on_sync_object(self, data):

        assert data['fsid'] == self.fsid

        sync_object = copy.deepcopy(data['data'])

        sync_type = SYNC_OBJECT_STR_TYPE[data['type']]
        new_object = self.inject_sync_object(
            data['type'], data['version'], sync_object
        )
        self._request_coll.on_map(sync_type, new_object)
        if new_object:
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
                util_data = self._get_utilization_data()
                NS.ceph.objects.Utilization(
                    total=util_data['cluster']['total'],
                    used=util_data['cluster']['used'],
                    available=util_data['cluster']['available'],
                    pcnt_used=util_data['cluster']['pcnt_used']
                ).save(update=False)

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
                    pool_used = 0
                    pcnt = 0
                    for pool in util_data['pools']:
                        if pool['name'] == raw_pool['pool_name']:
                            pool_used = pool['used']
                            pcnt = pool['pcnt_used']
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
                        used=pool_used,
                        percent_used=pcnt
                    ).save()
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
                    NS.ceph.objects.Osd(
                        id=raw_osd['osd'],
                        uuid=raw_osd['uuid'],
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
                    priority="warning",
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
                if cmd_out['err'] == "":
                    rbd_details[rbd]['provisioned'] = \
                        cmd_out['out'].split('\n')[1].split()[1]
                    rbd_details[rbd]['used'] = \
                        cmd_out['out'].split('\n')[1].split()[2]

        return rbd_details

    def _get_utilization_data(self):
        from ceph_argparse import json_command
        import rados
        cluster_handle = rados.Rados(
            name=ceph.RADOS_NAME,
            clustername=self.name,
            conffile=''
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
            raise rados.Error(outs)
        else:
            outbuf = outbuf.replace('RAW USED', 'RAW_USED')
            outbuf = outbuf.replace('%RAW USED', '%RAW_USED')
            outbuf = outbuf.replace('MAX AVAIL', 'MAX_AVAIL')
            lines = outbuf.split('\n')
            index = 0
            cluster_stat = {}
            pool_stat = []
            pool_stat_available = False
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
                                priority="warning",
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
                                priority="warning",
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
                                priority="warning",
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
                                priority="warning",
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
                                priority="warning",
                                publisher=NS.publisher_id,
                                payload={"message": "Missing fields in pool"
                                                    " stat"
                                         }
                            )
                        )
                        return {'cluster': cluster_stat, 'pools': {}}
                    dict = {}
                    dict['name'] = pool_fields[pool_name_idx]
                    dict['available'] = self._to_bytes(
                        pool_fields[pool_max_avail_idx]
                    )
                    dict['used'] = self._to_bytes(
                        pool_fields[pool_used_idx]
                    )
                    dict['pcnt_used'] = pool_fields[pool_pcnt_used_idx]
                    pool_stat.append(dict)
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
