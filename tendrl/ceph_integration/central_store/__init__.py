from tendrl.commons import central_store


class CephIntegrationEtcdCentralStore(central_store.EtcdCentralStore):
    def __init__(self):
        super(CephIntegrationEtcdCentralStore, self).__init__()

    def save_syncobject(self, sync_object):
        tendrl_ns.etcd_orm.save(sync_object)

    def save_globaldetails(self, details):
        tendrl_ns.etcd_orm.save(details)

    def save_config(self, config):
        tendrl_ns.etcd_orm.save(config)

    def save_server(self, server):
        tendrl_ns.etcd_orm.save(server)

    def save_service(self, service):
        tendrl_ns.etcd_orm.save(service)

    def save_events(self, events):
        for event in events:
            tendrl_ns.etcd_orm.save(event)

    def save_tendrlcontext(self, context):
        tendrl_ns.etcd_orm.save(context)

    def save_definition(self, definition):
        tendrl_ns.etcd_orm.save(definition)

    def save_pool(self, pool):
        tendrl_ns.etcd_orm.save(pool)

    def save_nodecontext(self, node_context):
        tendrl_ns.etcd_orm.save(node_context)

    def save_rbd(self, rbd):
        tendrl_ns.etcd_orm.save(rbd)

    def save_ecprofile(self, ec_profile):
        tendrl_ns.etcd_orm.save(ec_profile)

    def save_utilization(self, utilization):
        tendrl_ns.etcd_orm.save(utilization)

    def save_job(self, job):
        tendrl_ns.etcd_orm.save(job)
