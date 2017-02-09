# flake8: noqa
data = """---
namespace.tendrl.ceph_integration:
  flows:
    CreatePool:
      atoms:
        - tendrl.ceph_integration.objects.Pool.atoms.create.Create
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
    NodeContext:
      attrs:
        machine_id:
          help: "Unique /etc/machine-id"
          type: String
        fqdn:
          help: "FQDN of the Tendrl managed node"
          type: String
        node_id:
          help: "Tendrl ID for the managed node"
          type: String
        tags:
          help: "The tags associated with this node"
          type: String
        status:
          help: "Node status"
          type: String

      enabled: true
      list: clusters/$TendrlContext.integration_id/nodes/$NodeContext.node_id/NodeContext
      value: clusters/$TendrlContext.integration_id/nodes/$NodeContext.node_id/NodeContext
      help: Node Context

    SyncObject:
      attrs:
        updated:
          help: "Updated"
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

    Config:
      enabled: True
      help: "Config"
      value: _tendrl/definitions/master
      list: _tendrl/definitions/master
      attrs:
        master:
          help: master definitions
          type: String

    Rbd:
      atoms:
        Create:
          enabled: true
          help: "Create rbd"
          inputs:
            mandatory:
              - Rbd.pool_id
              - Rbd.name
              - Rbd.size
          name: "Create Rbd"
          run: tendrl.ceph_integration.objects.Rbd.atoms.create.Create
          type: Create
          uuid: 7a2df258-9b24-4fd3-a66f-ee346e2e3720
        Delete:
          enabled: true
          help: "Delete rbd"
          inputs:
            mandatory:
              - Rbd.pool_id
              - Rbd.name
          name: "Delete Rbd"
          run: tendrl.ceph_integration.objects.Rbd.atoms.delete.Delete
          type: Delete
          uuid: 7a2df258-9b24-4fd3-a66f-ee346e2e3721
        Resize:
          enabled: true
          help: "Resize Rbd"
          inputs:
            mandatory:
              - Rbd.pool_id
              - Rbd.name
              - Rbd.size
          name: "Resize Rbd"
          run: tendrl.ceph_integration.objects.Rbd.atoms.resize.Resize
          type: Update
          uuid: 7a2df258-9b24-4fd3-a66f-ee346e2e3722
      flows:
        CreateRbd:
          atoms:
            - tendrl.ceph_integration.objects.Rbd.atoms.create.Create
          help: "Create Rbd"
          enabled: true
          inputs:
            mandatory:
              - Rbd.pool_id
              - Rbd.name
              - Rbd.size
          run: tendrl.ceph_integration.objects.Rbd.flows.create_rbd.CreateRbd
          type: Create
          uuid: 9bc41d8f-a0cf-420a-b2fe-18761e07f3d2
        DeleteRbd:
          atoms:
            - tendrl.ceph_integration.objects.Rbd.atoms.delete.Delete
          help: "Delete Rbd"
          enabled: true
          inputs:
            mandatory:
              - Rbd.pool_id
              - Rbd.name
          run: tendrl.ceph_integration.objects.Rbd.flows.delete_rbd.DeleteRbd
          type: Delete
          uuid: 4ac41d8f-a0cf-420a-b2fe-18761e07f3a7
        ResizeRbd:
          atoms:
            - tendrl.ceph_integration.objects.Rbd.atoms.resize.Resize
          help: "Resize Rbd"
          enabled: true
          inputs:
            mandatory:
              - Rbd.pool_id
              - Rbd.name
              - Rbd.size
          run: tendrl.ceph_integration.objects.Rbd.flows.resize_rbd.ResizeRbd
          type: Update
          uuid: 4ac41d8f-a0cf-420a-b2fe-18761e07f3c9
      attrs:
        name:
          help: Name of the rbd
          type: String
        size:
          help: Size of the rbd (MB)
          type: int
        pool_id:
          help: Id of the pool
          type: String
        order:
          help: Order of the rbd
          type: String
        block_name_prefix:
          help: Prefix for the block name
          type: String
        format:
          help: format of rbd
          type: int
        features:
          help: featutres for rbd
          type: list
        flags:
          help: flags for rbd
          type: list
        provisioned:
          help: provisioned size
          type: int
        used:
          help: used size
          type: int
      help: "Rbd"
      enabled: true
      value: clusters/$TendrlContext.integration_id/Pools/$Pool.pool_id/rbds/$Rbd.name
      list: clusters/$TendrlContext.integration_id/Pools/$Pool.pool_id/rbds

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
              - Pool.type
              - Pool.erasure_code_profile
              - Pool.quota_enabled
              - Pool.quota_max_objects
              - Pool.quota_max_bytes
          name: "Create Pool"
          run: tendrl.ceph_integration.objects.Pool.atoms.create.Create
          type: Create
          uuid: bd0155a8-ff15-42ff-9c76-5176f53c13e0
        Delete:
          enabled: true
          help: "Pool delete Atom"
          inputs:
            mandatory:
              - Pool.pool_id
          name: "Delete Pool"
          run: tendrl.ceph_integration.objects.Pool.atoms.delete.Delete
          type: Delete
          uuid: 9a2df258-9b24-4fd3-a66f-ee346e2e3720
        Update:
          enabled: true
          help: "Pool update Atom"
          inputs:
            mandatory:
              - Pool.pool_id
            optional:
              - Pool.poolname
              - Pool.size
              - Pool.pg_num
              - Pool.quota_enabled
              - Pool.quota_max_objects
              - Pool.quota_max_bytes
          name: "Update Pool"
          run: tendrl.ceph_integration.objects.Pool.atoms.update.Update
          type: Update
          uuid: 9a2df258-9b24-4fd3-a66f-ee346e2e3721
      flows:
        DeletePool:
          atoms:
            - tendrl.ceph_integration.objects.Pool.atoms.delete.Delete
          help: "Delete Ceph Pool"
          enabled: true
          inputs:
            mandatory:
              - Pool.pool_id
              - TendrlContext.sds_name
              - TendrlContext.sds_version
              - TendrlContext.integration_id
          run: tendrl.ceph_integration.objects.Pool.flows.delete_pool.DeletePool
          type: Delete
          uuid: 4ac41d8f-a0cf-420a-b2fe-18761e07f3b9
        UpdatePool:
          atoms:
            - tendrl.ceph_integration.objects.Pool.atoms.update.Update
          help: "Update Ceph Pool"
          enabled: true
          inputs:
            mandatory:
              - Pool.pool_id
            optional:
              - Pool.poolname
              - Pool.size
              - Pool.pg_num
              - Pool.quota_enabled
              - Pool.quota_max_objects
              - Pool.quota_max_bytes
          run: tendrl.ceph_integration.objects.Pool.flows.update_pool.UpdatePool
          type: Update
          uuid: 4ac41d8f-a0cf-420a-b2fe-18761e07f3b2
      attrs:
        crush_ruleset:
          help: "The ID of a CRUSH ruleset to use for this pool. The specified ruleset must exist."
          type: Integer
        erasure_code_profile:
          help: "For erasure pools only.It must be an existing profile "
          type: String
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
        type:
          help: "Type of the Ceph pool(ec or replicated)"
          type: String
        replica_count:
          help: "Replica count of volume"
          type: Integer
        size:
          help: "Sets the minimum number of replicas required for I/O"
          type: Integer
        quota_enabled:
          help: if quota enabled for the pool
          type: bool
        quota_max_objects:
          help: maximum no of object
          type: int
        quota_max_bytes:
          help: maximum no of bytes
          type: int
      help: "Pool"
      enabled: true
      value: clusters/$TendrlContext.integration_id/Pools/$Pool.pool_id
      list: clusters/$TendrlContext.integration_id/Pools

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
tendrl_schema_version: 0.3
"""
