from tendrl.ceph_integration.flows.flow import Flow


class DeletePool(Flow):
    def run(self):
        super(DeletePool, self).run()
