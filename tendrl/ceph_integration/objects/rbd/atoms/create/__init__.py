from sets import Set

import etcd

from tendrl.ceph_integration.manager.crud import Crud
from tendrl.ceph_integration.manager.exceptions import \
    RequestStateError
from tendrl.ceph_integration.objects.pool import Pool
from tendrl.commons.event import Event
from tendrl.commons.message import Message
from tendrl.commons import objects
from tendrl.commons.objects.job import Job
import uuid


class Create(objects.BaseAtom):

    def __init__(self, *args, **kwargs):
        super(Create, self).__init__(*args, **kwargs)

    def run(self):
        Event(
            Message(
                priority="info",
                publisher=NS.publisher_id,
                payload={
                    "message": "Checking if a new  pool has to be created or "
                               "not for rbd creation"
                },
                job_id=self.parameters['job_id'],
                flow_id=self.parameters['flow_id'],
                cluster_id=NS.tendrl_context.integration_id,
            )
        )
        if not self.parameters.get('Rbd.pool_id'):
            # Checking if mandatory parameters for pool creation are present
            mandatory_pool_params = Set(["Rbd.pool_poolname",
                                         "Rbd.pool_pg_num",
                                         "Rbd.pool_size",
                                         "Rbd.pool_min_size"])
            missing_params = list(mandatory_pool_params.difference(
                Set(self.parameters.keys())))
            if not missing_params:
                # Mapping the passed pool parameters into required keys
                pool_parameters = {}
                for key, value in self.parameters.items():
                    if "Rbd.pool_" in key:
                        pool_parameters[key.replace("Rbd.pool_", "Pool.")] =\
                            value
                payload = {
                    "integration_id": NS.tendrl_context.integration_id,
                    "run": "ceph.flows.CreatePool",
                    "status": "new",
                    "parameters": pool_parameters,
                    "parent": self.parameters['job_id'],
                    "type": "sds",
                    "tags": ["tendrl/integration/$TendrlContext."
                             "integration_id"]
                }
                Event(
                    Message(
                        priority="error",
                        publisher=NS.publisher_id,
                        payload={
                            "message": "Creating job for pool creation"
                        },
                        job_id=self.parameters['job_id'],
                        flow_id=self.parameters['flow_id'],
                        cluster_id=NS.tendrl_context.integration_id,
                    )
                )
                _job_id = str(uuid.uuid4())
                Job(job_id=_job_id,
                    status="new",
                    payload=payload).save()
                Event(
                    Message(
                        priority="error",
                        publisher=NS.publisher_id,
                        payload={
                            "message": "Checking for successful pool creation"
                        },
                        job_id=self.parameters['job_id'],
                        flow_id=self.parameters['flow_id'],
                        cluster_id=NS.tendrl_context.integration_id,
                    )
                )
                pool_created = False
                job_status = "new"
                while not pool_created:
                    try:
                        job_status = NS._int.client.read(
                            "/queue/%s/status" % _job_id).value
                    except etcd.EtcdKeyNotFound:
                        Event(
                            Message(
                                priority="error",
                                publisher=NS.publisher_id,
                                payload={
                                    "message": "Failed to fetch pool "
                                               "creation status for rbd "
                                               "creation"
                                },
                                job_id=self.parameters['job_id'],
                                flow_id=self.parameters['flow_id'],
                                cluster_id=NS.tendrl_context.integration_id,
                            )
                        )
                        break
                    if job_status == "finished":
                        pool_created = True
                    elif job_status == "failed":
                        break
                if pool_created:
                    # Setting pool_id for rbd creation
                    pool_id = self._get_pool_id(self.parameters[
                        'Rbd.pool_poolname'])
                    if pool_id:
                        self.parameters['Rbd.pool_id'] = pool_id
                    else:
                        Event(
                            Message(
                                priority="error",
                                publisher=NS.publisher_id,
                                payload={
                                    "message": "Failed to fetch pool_id %s ."
                                               "Cannot create rbd without "
                                               "pool_id." % pool_id
                                },
                                job_id=self.parameters['job_id'],
                                flow_id=self.parameters['flow_id'],
                                cluster_id=NS.tendrl_context.integration_id,
                            )
                        )
                        return False
                else:
                    Event(
                        Message(
                            priority="error",
                            publisher=NS.publisher_id,
                            payload={
                                "message": "Failed to create pool. "
                                           "Cannot proceed with rbd creation."
                            },
                            job_id=self.parameters['job_id'],
                            flow_id=self.parameters['flow_id'],
                            cluster_id=NS.tendrl_context.integration_id,
                        )
                    )
                    return False
            else:
                Event(
                    Message(
                        priority="info",
                        publisher=NS.publisher_id,
                        payload={
                            "message": "Mandatory parameters %s for pool "
                                       "creation not present. Cannot continue"
                                       " with rbd creation." %
                                       ', '.join(missing_params)
                        },
                        job_id=self.parameters['job_id'],
                        flow_id=self.parameters['flow_id'],
                        cluster_id=NS.tendrl_context.integration_id,
                    )
                )
                return False

        attrs = dict(name=self.parameters['Rbd.name'],
                     size=str(self.parameters['Rbd.size']),
                     pool_id=self.parameters.get('Rbd.pool_id')
                     )
        Event(
            Message(
                priority="info",
                publisher=NS.publisher_id,
                payload={
                    "message": "Creating rbd %s on pool %s" %
                    (self.parameters['Rbd.name'],
                     self.parameters['Rbd.pool_id'])
                },
                job_id=self.parameters['job_id'],
                flow_id=self.parameters['flow_id'],
                cluster_id=NS.tendrl_context.integration_id,
            )
        )

        crud = Crud()
        resp = crud.create("rbd", attrs)
        try:
            crud.sync_request_status(resp['request'])
        except RequestStateError as ex:
            Event(
                Message(
                    priority="info",
                    publisher=NS.publisher_id,
                    payload={
                        "message": "Failed to create rbd %s."
                        " Error: %s" % (self.parameters['Rbd.name'],
                                        ex)
                    },
                    job_id=self.parameters['job_id'],
                    flow_id=self.parameters['flow_id'],
                    cluster_id=NS.tendrl_context.integration_id,
                )
            )
            return False

        Event(
            Message(
                priority="info",
                publisher=NS.publisher_id,
                payload={
                    "message": "Successfully created rbd %s on pool %s" %
                    (self.parameters['Rbd.name'],
                     self.parameters['Rbd.pool_id'])
                },
                job_id=self.parameters['job_id'],
                flow_id=self.parameters['flow_id'],
                cluster_id=NS.tendrl_context.integration_id,
            )
        )

        pool_name = NS._int.client.read(
            "clusters/%s/Pools/%s/pool_name" %
            (NS.tendrl_context.integration_id,
             self.parameters['Rbd.pool_id'])
        ).value
        rbd_details = NS.state_sync_thread._get_rbds(pool_name)
        for k, v in rbd_details.iteritems():
            NS.ceph.objects.Rbd(
                name=k,
                size=v['size'],
                pool_id=self.parameters['Rbd.pool_id'],
                flags=v['flags'],
                provisioned=NS.state_sync_thread._to_bytes(
                    v['provisioned']),
                used=NS.state_sync_thread._to_bytes(v['used'])
            ).save()

        return True

    def _get_pool_id(self, pool_name):
        try:
            pools = NS._int.client.read(
                "clusters/%s/Pools" % NS.tendrl_context.integration_id
            )
        except etcd.EtcdKeyNotFound:
            return False

        for pool in pools.leaves:
            fetched_pool = Pool(pool_id=pool.key.split("Pools/")[-1]).load()
            if fetched_pool.pool_name == pool_name:
                Event(
                    Message(
                        priority="info",
                        publisher=NS.publisher_id,
                        payload={
                            "message": "Found pool_id with pool_name %s" %
                            pool_name
                        },
                        job_id=self.parameters['job_id'],
                        flow_id=self.parameters['flow_id'],
                        cluster_id=NS.tendrl_context.integration_id,
                    )
                )
                return fetched_pool.pool_id
