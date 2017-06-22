import multiprocessing
import os
import rados
import rbd

from gevent import Timeout
from Queue import Empty

RADOS_TIMEOUT = 20
RADOS_NAME = 'client.admin'
SRC_DIR = '/etc/ceph'


class RbdOperationTimout(Exception):
    pass


class ClusterHandle():

    def __init__(self, cluster_name):
        self.cluster_name = cluster_name

    def __enter__(self):
        if SRC_DIR:
            conf_file = os.path.join(SRC_DIR, self.cluster_name + ".conf")
        else:
            conf_file = ''

        self.cluster_handle = rados.Rados(
            name=RADOS_NAME,
            clustername=self.cluster_name,
            conffile=conf_file)
        self.cluster_handle.connect(timeout=RADOS_TIMEOUT)

        return self.cluster_handle

    def __exit__(self, *args):
        self.cluster_handle.shutdown()


def rbd_operation(cluster_name, attributes):
    err = None
    p = None
    queue = multiprocessing.Queue()
    if attributes['operation'] == "update":
        p = multiprocessing.Process(target=_update_rbd, args=(
            cluster_name, attributes))
    if attributes['operation'] == "create":
        p = multiprocessing.Process(target=_create_rbd, args=(
            cluster_name, attributes, queue))
    if attributes['operation'] == "delete":
        p = multiprocessing.Process(target=_delete_rbd, args=(
            cluster_name, attributes, queue))
    p.start()
    # Wait for 20 seconds or until process finishes
    p.join(20)
    # If thread is still active
    if p.is_alive():
        # Terminate
        p.terminate()
        err = "rbd command timed out"
    else:
        try:
            err = queue.get_nowait()
        except Empty:
            pass
    if err:
        result = dict({'status': 1,
                       'err': err})
    else:
        result = dict({'status': 0,
                       'err': ''})    
    return result


def _update_rbd(cluster_name, attributes):
    with ClusterHandle(cluster_name) as cluster:
        with cluster.open_ioctx(attributes['pool_name']) as ioctx:
            with rbd.Image(ioctx, attributes["name"]) as image:
                # converting bytes to gb
                size  = int(attributes['size']) * 1024 * 1024
                image.resize(size)


def _create_rbd(cluster_name, attributes, queue):
    with ClusterHandle(cluster_name) as cluster:
        with cluster.open_ioctx(attributes['pool_name']) as ioctx:
            try:
                # converting bytes to gb
                size  = int(attributes['size']) * 1024 * 1024
                rbd_inst = rbd.RBD()
                rbd_inst.create(ioctx, attributes['name'], size)
            except (rbd.ImageExists, TypeError,
                    rbd.InvalidArgument, rbd.FunctionNotSupported) as ex:
                queue.put(ex.message)


def _delete_rbd(cluster_name, attributes, queue):
    with ClusterHandle(cluster_name) as cluster:
        with cluster.open_ioctx(attributes['pool_name']) as ioctx:
            try:
                rbd_inst = rbd.RBD()
                rbd_inst.remove(ioctx, attributes['name'])
            except (rbd.ImageNotFound, rbd.ImageBusy,
                    rbd.ImageHasSnapshots) as ex:
                queue.put(ex.message)
