import json
import uuid

import etcd

job_id1 = str(uuid.uuid4())

job = {
    "cluster_id": "49fa2adde8a6e98591f0f5cb4bc5f44d",
    "run": "tendrl.gluster_integration.flows.create.CreatePool",
    "status": 'new',
    "parameters": {
        "Pool.poolname": 'test',
        "Pool.pg_num": 1,
        "Pool.min_size": 1,
        "Tendrl_context.sds_name": "ceph",
        "Tendrl_context.sds_version": "1",
        "Tendrl_context.cluster_id": "49fa2adde8a6e98591f0f5cb4bc5f44d"
    },
    type: "sds"
}


client = etcd.Client()
client.write("/queue/job_%s" % job_id1, json.dumps(job))
