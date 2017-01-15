from tendrl.ceph_integration.manager.crud import Crud
from tendrl.ceph_integration.manager import utils as manager_utils
from tendrl.commons.atoms.base_atom import BaseAtom


class Create(BaseAtom):
    def run(self, parameters):
        fsid = manager_utils.get_fsid()
        attrs = dict(name=parameters['Pool.poolname'],
                     pg_num=parameters['Pool.pg_num'],
                     min_size=parameters['Pool.min_size'])
        crud = Crud(parameters['manager'])
        crud.create(fsid, "pool", attrs)
        return True
