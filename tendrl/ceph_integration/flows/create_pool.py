from tendrl.ceph_integration.flows.flow import Flow


class CreatePool(Flow):
    def run(self):
        super(CreatePool, self).run()
