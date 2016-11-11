from tendrl.ceph_bridge.persistence import servers


class Test_Server(object):
    def test_Server(self):
        self.server = servers.Server()
        assert self.server.render() == [
            {
                'value': None,
                'dir': False,
                'name': 'boot_time',
                'key': '/clusters/ceph/None/\
servers/None/boot_time'
            },
            {
                'value': None,
                'dir': False,
                'name': 'ceph_version',
                'key': '/clusters/ceph/None/\
servers/None/ceph_version'
            },
            {
                'value': None,
                'dir': False,
                'name': 'fqdn',
                'key': '/clusters/ceph/None/\
servers/None/fqdn'
            },
            {
                'value': None,
                'dir': False,
                'name': 'fsid',
                'key': '/clusters/ceph/None/\
servers/None/fsid'
            },
            {
                'value': None,
                'dir': False,
                'name': 'hostname',
                'key': '/clusters/ceph/None/\
servers/None/hostname'
            },
            {
                'value': None,
                'dir': False,
                'name': 'last_contact',
                'key': '/clusters/ceph/None/\
servers/None/last_contact'
            },
            {
                'value': None,
                'dir': False,
                'name': 'managed',
                'key': '/clusters/ceph/None/servers/None/managed'
            }]


class Test_Service(object):
    def test_Service(self):
        self.service = servers.Service()
        assert self.service.render() == [
            {
                'value': None,
                'dir': False,
                'name': 'fsid',
                'key': '/clusters/ceph/None/\
services/None/None/None/fsid'
            },
            {
                'value': None,
                'dir': False,
                'name': 'running',
                'key': '/clusters/ceph/None/\
services/None/None/None/running'
            },
            {
                'value': None,
                'dir': False,
                'name': 'server_fqdn',
                'key': '/clusters/ceph/None/\
services/None/None/None/server_fqdn'
            },
            {
                'value': None,
                'dir': False,
                'name': 'server_uuid',
                'key': '/clusters/ceph/None/\
services/None/None/None/server_uuid'
            },
            {
                'value': None,
                'dir': False,
                'name': 'service_id',
                'key': '/clusters/ceph/None/\
services/None/None/None/service_id'
            },
            {
                'value': None,
                'dir': False,
                'name': 'service_type',
                'key': '/clusters/ceph/None/\
services/None/None/None/service_type'
            },
            {
                'value': None,
                'dir': False,
                'name': 'status',
                'key': '/clusters/ceph/None/\
services/None/None/None/status'
            }]
