from gevent.lock import RLock
from tendrl.ceph_integration.manager.user_request import UserRequest


class RequestCollection(object):

    def __init__(self):
        super(RequestCollection, self).__init__()
        self._by_request_id = {}
        self._lock = RLock()

    def get_by_id(self, request_id):
        return self._by_request_id[request_id]

    def get_all(self, state=None):
        if not state:
            return self._by_request_id.values()
        else:
            return [r for r in self._by_request_id.values()
                    if r.state == state]

    def on_map(self, sync_type, sync_object):
        with self._lock:
            requests = self.get_all(state=UserRequest.SUBMITTED)
            for request in requests:
                try:
                    # If this is one of the types that this request
                    # is waiting for, invoke on_map.
                    for awaited_type in request.awaiting_versions.keys():
                        if awaited_type == sync_type:
                            request.on_map(sync_type, sync_object)
                except Exception as e:
                    request.set_error("Internal error %s" % e)
                    request.complete()
