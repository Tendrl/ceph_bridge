class Create(object):
    def run(self, parameters):
        fsid = parameters['fsid']
        attrs = dict(name=parameters['Pool.poolname'],
                     pg_num=parameters['Pool.pg_num'],
                     min_size=parameters['Pool.min_size'])
        parameters['crud'].create(fsid, "pool", attrs)
        return True
