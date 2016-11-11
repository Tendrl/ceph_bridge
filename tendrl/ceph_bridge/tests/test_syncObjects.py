from tendrl.ceph_bridge.persistence.sync_objects import SyncObject


class Test_SyncObject(object):

    def test_SyncObject(self):
        self.sync_object = SyncObject()
        assert self.sync_object.render() == [
            {
                'name': 'cluster_name',
                'key': '/clusters/ceph/fsid/maps/sync_type/cluster_name',
                'dir': False,
                'value': 'name'
            },
            {
                'name': 'data',
                'key': '/clusters/ceph/fsid/maps/sync_type/data',
                'dir': False,
                'value': 'data'
            },
            {
                'name': 'fsid',
                'key': '/clusters/ceph/fsid/maps/sync_type/fsid',
                'dir': False,
                'value': 'fsid'
            },
            {
                'name': 'sync_type',
                'key': '/clusters/ceph/fsid/maps/sync_type/sync_type',
                'dir': False,
                'value': 'sync_type'
            },
            {
                'name': 'updated',
                'key': '/clusters/ceph/fsid/maps/sync_type/updated',
                'dir': False,
                'value': 'updated'
            },
            {
                'name': 'version',
                'key': '/clusters/ceph/fsid/maps/sync_type/version',
                'dir': False,
                'value': 'version'
            },
            {
                'name': 'when',
                'key': '/clusters/ceph/fsid/maps/sync_type/when',
                'dir': False,
                'value': 'when'
            }]
