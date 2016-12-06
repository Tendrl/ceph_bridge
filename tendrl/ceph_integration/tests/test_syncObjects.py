from tendrl.ceph_integration.persistence.sync_objects import SyncObject


class Test_SyncObject(object):

    def test_SyncObject(self):
        self.sync_object = SyncObject()
        assert self.sync_object.render() == [
            {
                'name': 'cluster_id',
                'key': '/clusters/cluster_id/maps/sync_type/cluster_id',
                'dir': False,
                'value': 'cluster_id'
            },
            {
                'name': 'cluster_name',
                'key': '/clusters/cluster_id/maps/sync_type/cluster_name',
                'dir': False,
                'value': 'name'
            },
            {
                'name': 'data',
                'key': '/clusters/cluster_id/maps/sync_type/data',
                'dir': False,
                'value': 'data'
            },
            {
                'name': 'fsid',
                'key': '/clusters/cluster_id/maps/sync_type/fsid',
                'dir': False,
                'value': 'fsid'
            },
            {
                'name': 'sync_type',
                'key': '/clusters/cluster_id/maps/sync_type/sync_type',
                'dir': False,
                'value': 'sync_type'
            },
            {
                'name': 'updated',
                'key': '/clusters/cluster_id/maps/sync_type/updated',
                'dir': False,
                'value': 'updated'
            },
            {
                'name': 'version',
                'key': '/clusters/cluster_id/maps/sync_type/version',
                'dir': False,
                'value': 'version'
            },
            {
                'name': 'when',
                'key': '/clusters/cluster_id/maps/sync_type/when',
                'dir': False,
                'value': 'when'
            }]
