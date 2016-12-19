import collectd
import json
import subprocess


STATS = "stats"
POOLS = "pools"
NAME = "name"
BYTES_USED = "bytes_used"
MAX_AVAIL = "max_avail"
CLUSTER_NAME = "cluster_name"
TOTAL_BYTES = "total_bytes"
USED_BYTES = "total_used_bytes"
AVAILABLE_BYTES = "total_avail_bytes"
INTERVAL = "interval"
CLUSTER_UTILIZATION = "cluster_utilization"
POOL_UTILIZATION = "pool_utilization"


class CephCollectdUtilizations(object):

    def __init__(self):
        self.cluster_name = "ceph01"
        self.interval = 6


    def configure_callback(self, config):
        for node in config.children:
            if node.key == "CLUSTER_NAME":
                self.cluster_name = node.values[0]
            if node.key == "INTERVAL":
                self.interval = node.values[0]


    def sendMetric(self, plugin_name, instance_name, value):
        metric = collectd.Values()
        metric.plugin = plugin_name
        metric.host = self.cluster_name
        metric.type = 'gauge'
        metric.values = [value]
        metric.type_instance = instance_name
        metric.dispatch()


def getUtilization(cluster_name):
    cmd = "ceph df --cluster %s --format=json" %(cluster_name)
    try:
        result = json.loads(subprocess.check_output(cmd.split()))
    except Exception as e:
        collectd.error("Failed to fetch cluster and pool utilization. The command returned %s.The error is %s" %(result, e.output))
    return result


def read_callback():
    stats = getUtilization(collectdPlugin.cluster_name)
    if STATS in stats:
        if TOTAL_BYTES in stats[STATS]:
            collectdPlugin.sendMetric(CLUSTER_UTILIZATION, TOTAL_BYTES, stats[STATS][TOTAL_BYTES])
        if USED_BYTES in stats[STATS]:
            collectdPlugin.sendMetric(CLUSTER_UTILIZATION, USED_BYTES, stats[STATS][USED_BYTES])
        if AVAILABLE_BYTES in stats[STATS]:
            collectdPlugin.sendMetric(CLUSTER_UTILIZATION, AVAILABLE_BYTES, stats[STATS][AVAILABLE_BYTES])
    if POOLS in stats:
    	for pool in stats[POOLS]:
    		if NAME in pool:
    			if STATS in pool:
    				if BYTES_USED in pool[STATS]:
    					collectdPlugin.sendMetric(POOL_UTILIZATION, pool[NAME] + "." + USED_BYTES, pool[STATS][BYTES_USED])
    				if MAX_AVAIL in pool[STATS]:
    					collectdPlugin.sendMetric(POOL_UTILIZATION, pool[NAME] + "." + AVAILABLE_BYTES, pool[STATS][MAX_AVAIL])


def configure_callback(config):
    collectdPlugin.configure_callback(config)


collectdPlugin = CephCollectdUtilizations()
collectd.register_config(configure_callback)
collectd.register_read(read_callback, collectdPlugin.interval)