from tendrl.ceph_integration.manager import crud


class RbdCrud(crud.Crud):

    def __init__(self):
        super(RbdCrud, self).__init__()

    def delete_rbd(self, pool_id, rbd_name):
        return NS.state_sync_thread.request_rbd_delete(
            pool_id,
            rbd_name
        )
