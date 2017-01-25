# flake8: noqa
data = """---
namespace.tendrl.ceph_integration:
  flows:
    CreatePool:
      atoms:
        - tendrl.ceph_integration.objects.pool.atoms.create
      help: "Create Ceph Pool"
      enabled: true
      inputs:
        mandatory:
          - Pool.poolname
          - Pool.pg_num
          - Pool.min_size
          - TendrlContext.sds_name
          - TendrlContext.sds_version
          - TendrlContext.integration_id
      run: tendrl.ceph_integration.flows.create_pool.CreatePool
      type: Create
      uuid: faeab231-69e9-4c9d-b5ef-a67ed057f98b
  objects:
    Config:
      enabled: True
      help: "Config"
      value: _tendrl/definitions/master
      list: _tendrl/definitions/master
      attrs:
        master:
          help: master definitions
          type: String
    Pool:
      atoms:
        Create:
          enabled: true
          help: "Pool create Atom"
          inputs:
            mandatory:
              - Pool.poolname
              - Pool.pg_num
              - Pool.min_size
            optional:
              - Pool.max_objects
              - Pool.max_bytes
              - Pool.ec_profile
          name: "Create Pool"
          run: tendrl.ceph_integration.objects.pool.atoms.create.Create
          type: Create
          uuid: bd0155a8-ff15-42ff-9c76-5176f53c13e0
        Delete:
          enabled: true
          help: "Pool delete Atom"
          inputs:
            mandatory:
              - Pool.pool_id
          name: "Delete Pool"
          run: tendrl.ceph_integration.objects.pool.atoms.delete.Delete
          type: Delete
          uuid: 9a2df258-9b24-4fd3-a66f-ee346e2e3720
      flows:
        DeletePool:
          atoms:
            - tendrl.ceph_integration.objects.pool.atoms.delete
          help: "Delete Ceph Pool"
          enabled: true
          inputs:
            mandatory:
              - Pool.pool_id
              - TendrlContext.sds_name
              - TendrlContext.sds_version
              - TendrlContext.integration_id
          run: tendrl.ceph_integration.objects.pool.flows.delete_pool.DeletePool
          type: Delete
          uuid: 4ac41d8f-a0cf-420a-b2fe-18761e07f3b9
      attrs:
        crush_ruleset:
          help: "The ID of a CRUSH ruleset to use for this pool. The specified ruleset must exist."
          type: Integer
        ec_profile:
          help: "For erasure pools only.It must be an existing profile "
          type: String
        max_bytes:
          help: "quota for maximum number of bytes. To remove quota set the value to zero"
          type: Integer
        max_objects:
          help: "quota for maximum number of objects. To remove quota set the value to zero"
          type: Integer
        min_size:
          help: "sets the number of replicas for objects in the pool"
          type: Integer
        pg_num:
          help: "The total number of placement groups for placement purposes."
          type: Integer
        pgp_num:
          help: "The total number of placement groups for the pool."
          type: Integer
        pool_id:
          help: "id of the pool"
          type: Integer
        poolname:
          help: "Name of the Ceph pool"
          type: String
        pooltype:
          help: "Type of the Ceph pool(ec or replicated)"
          type: String
        replica_count:
          help: "Replica count of volume"
          type: Integer
        size:
          help: "Sets the minimum number of replicas required for I/O"
          type: Integer
      help: "Pool"
      enabled: true
      value: clusters/$TendrlContext.integration_id/maps/osd_map/data
    TendrlContext:
      attrs:
        integration_id:
          help: "Tendrl managed/generated cluster id for the sds being managed by Tendrl"
          type: String
        sds_name:
          help: gluster|ceph
          type: String
        sds_version:
          help: "Sds version eg: 1.2.3"
          type: String
      help: "Tendrl Context "
      enabled: true
      value: clusters/$TendrlContext.integration_id/TendrlContext/
    SyncObject:
      attrs:
        fsid:
          help: "Tendrl managed/generated cluster id for the sds being managed by Tendrl"
          type: String
        cluster_name:
          help: gluster|ceph
          type: String
        sync_type:
          help: "Sync Type eg: Mon Map, OSD Map etc"
          type: String
        version:
          help: "version of sync type eg: 1.2.3"
          type: String
        when:
          help: "time of data collection"
          type: String
        data:
          help: "Sync data"
          type: String
      help: "Cluster sync data "
      enabled: true
      value: clusters/$TendrlContext.integration_id/maps/$SyncObject.sync_type
tendrl_schema_version: 0.3
"""
