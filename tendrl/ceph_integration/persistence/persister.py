from tendrl.ceph_integration.persistence.sync_objects import SyncObject
from tendrl.commons.etcdobj.etcdobj import Server as etcd_server
from tendrl.commons.persistence.etcd_persister import EtcdPersister


class CephIntegrationEtcdPersister(EtcdPersister):
    def __init__(self, config):
        etcd_kwargs = {
            'port': int(config["configuration"]["etcd_port"]),
            'host': config["configuration"]["etcd_connection"]
        }
        self._store = etcd_server(etcd_kwargs=etcd_kwargs)
        super(CephIntegrationEtcdPersister, self).__init__(self._store.client)

    def update_sync_object(
        self,
        updated,
        fsid,
        name,
        sync_type,
        version,
        when,
        data,
        cluster_id
    ):
        self._store.save(
            SyncObject(
                updated=updated,
                fsid=fsid,
                cluster_name=name,
                sync_type=sync_type,
                version=version,
                when=when,
                data=data,
                cluster_id=cluster_id
            )
        )

    def create_server(self, server):
        self._store.save(server)

    def create_service(self, service):
        self._store.save(service)

    def save_events(self, events):
        for event in events:
            self._store.save(event)

    def update_tendrl_context(self, context):
        self._store.save(context)

    def update_tendrl_definitions(self, definition):
        self._store.save(definition)

    def update_pool(self, pool):
        self._store.save(pool)
