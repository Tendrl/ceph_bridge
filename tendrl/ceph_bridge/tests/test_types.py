from mock import MagicMock
import pytest
from tendrl.ceph_bridge.tests.util import load_fixture
from tendrl.ceph_bridge.types import MonStatus
from tendrl.ceph_bridge.types import OsdMap


# An OSD map with some non-default CRUSH rules in it
INTERESTING_OSD_MAP = load_fixture('interesting_osd_map.json')


class TestOsdMap(object):
    """Tests for the processing that we do on the OSD map to expose

    higher level views.
    """

    def test_crush_osds(self):
        """That the correct OSDs are recognised as part of a CRUSH rule

        """
        osd_map = OsdMap(None, None)  # None data
        assert isinstance(osd_map, OsdMap)

        osd_map = OsdMap(None, INTERESTING_OSD_MAP)

        all_osds = [0, 1, 2, 3, 4, 5]
        first_osds = [0, 2, 4]
        first_server_osds = [0, 1]

        assert osd_map.osds_by_rule_id == ({
            # Default rule
            0: all_osds,
            # Default rule
            1: all_osds,
            # Default rule
            2: all_osds,
            # My custom one that takes each server's first drive
            3: first_osds,
            # My custom one that takes the drives from the first server
            4: first_server_osds
        })

        # By extension, the same OSDs should be recognised as part of
        # the pools using the crush rule
        assert osd_map.osds_by_pool == ({
            2: all_osds,
            4: all_osds,
            5: all_osds,
            6: first_osds,
            7: first_server_osds
        })
        assert osd_map.osd_pools == (
            {
                0: [2, 4, 5, 6, 7],
                1: [2, 4, 5, 7],
                2: [2, 4, 5, 6],
                3: [2, 4, 5],
                4: [2, 4, 5, 6],
                5: [2, 4, 5]
            })

    def test_7883(self):
        """Bug in which pools were not found for OSDs"""
        osd_map = OsdMap(None, load_fixture("osd_map-7883.json"))
        all_osds = osd_map.osds_by_id.keys()
        assert len(all_osds) == 168

        assert osd_map.osds_by_rule_id == ({
            0: all_osds,
            1: all_osds,
            2: all_osds
        })

        assert osd_map.osds_by_pool == ({
            0: all_osds,
            1: all_osds,
            2: all_osds
        })


class TestCrushNodes(object):

    def setup_method(self, method):
        self.osd_map_data = MagicMock()
        self.osd_map_data.__getitem__.side_effect = lambda x: \
            self.data[x] if x in self.data else self.osd_map_data

    def test_parent_map_none(self):
        self.data = {'tree': {'nodes': []}}
        osd_map = OsdMap(None, self.osd_map_data)
        assert {} == osd_map.parent_bucket_by_node_id

    def test_parent_map_one(self):
        self.data = {'tree': {'nodes': [
            {"children": [],
             "type": "rack",
             "id": -5,
             "name": "83988b9c-4a63-11e4-8c64-000c29066317",
             "type_id": 2,
             },
            {"children": [-5],
             "type": "root",
             "id": -1,
             "name": "default",
             "type_id": 6,
             }
        ]}}

        osd_map = OsdMap(None, self.osd_map_data)
        assert osd_map.parent_bucket_by_node_id == (
            {
                -5: [{'type_id': 6,
                      'type': 'root',
                      'children': [-5],
                      'name': 'default',
                      'id': -1
                      }]
            })

    def test_parent_map_some(self):
        self.data = {'tree': {'nodes': [
            {"children": [-4, -3, -2],
             "type": "root",
             "id": -1,
             "name": "default",
             "type_id": 6
             }
        ]}}

        osd_map = OsdMap(None, self.osd_map_data)
        assert osd_map.parent_bucket_by_node_id == (
            {
                -4: [{'type_id': 6,
                      'type': 'root',
                      'children': [-4, -3, -2],
                      'name': 'default',
                      'id': -1
                      }],
                -3: [{'type_id': 6,
                      'type': 'root',
                      'children': [-4, -3, -2],
                      'name': 'default',
                      'id': -1
                      }],
                -2: [{'type_id': 6,
                      'type': 'root',
                      'children': [-4, -3, -2],
                      'name': 'default',
                      'id': -1
                      }]
            })

    def test_parent_map_many(self):
        self.data = {'tree': {'nodes': [
            {
                "children": [],
                "type": "rack",
                "id": -5,
                "name": "83988b9c-4a63-11e4-8c64-000c29066317",
                "type_id": 2
            },
            {
                "children": [
                    -4,
                    -2,
                    -3
                ],
                "type": "root",
                "id": -1,
                "name": "default",
                "type_id": 6
            },
            {
                "children": [
                    1
                ],
                "type": "host",
                "id": -3,
                "name": "vpm068",
                "type_id": 1
            },
            {
                "status": "up",
                "name": "osd.1",
                "exists": 1,
                "reweight": "1.000000",
                "type_id": 0,
                "crush_weight": "0.399994",
                "depth": 2,
                "type": "osd",
                "id": 1
            },
            {
                "children": [
                    0
                ],
                "type": "host",
                "id": -2,
                "name": "vpm114",
                "type_id": 1
            },
            {
                "status": "up",
                "name": "osd.0",
                "exists": 1,
                "reweight": "1.000000",
                "type_id": 0,
                "crush_weight": "0.099991",
                "depth": 2,
                "type": "osd",
                "id": 0
            },
            {
                "children": [
                    2
                ],
                "type": "host",
                "id": -4,
                "name": "vpm140",
                "type_id": 1
            },
            {
                "status": "up",
                "name": "osd.2",
                "exists": 1,
                "reweight": "1.000000",
                "type_id": 0,
                "crush_weight": "0.099991",
                "depth": 2,
                "type": "osd",
                "id": 2
            }
        ]}}

        osd_map = OsdMap(None, self.osd_map_data)
        assert osd_map.parent_bucket_by_node_id == (
            {
                0: [{'type_id': 1,
                     'type': 'host',
                     'children': [0],
                     'name': 'vpm114',
                     'id': -2
                     }],
                1: [{'type_id': 1,
                     'type': 'host',
                     'children': [1],
                     'name': 'vpm068',
                     'id': -3
                     }],
                2: [{'type_id': 1,
                     'type': 'host',
                     'children': [2],
                     'name': 'vpm140',
                     'id': -4
                     }],
                -4: [{'type_id': 6,
                      'type': 'root',
                      'children': [-4, -2, -3],
                      'name': 'default',
                      'id': -1
                      }],
                -3: [{'type_id': 6,
                      'type': 'root',
                      'children': [-4, -2, -3],
                      'name': 'default',
                      'id': -1
                      }],
                -2: [{'type_id': 6,
                      'type': 'root',
                      'children': [-4, -2, -3],
                      'name': 'default',
                      'id': -1
                      }]
            })

    def test_parent_map_multiple_roots(self):
        self.data = {"tree": {"nodes": [
            {
                "children": [
                    2
                ],
                "type": "host",
                "id": -40,
                "name": "vpm145ssd",
                "type_id": 1
            },
            {
                "status": "up",
                "name": "osd.2",
                "exists": 1,
                "reweight": "1.000000",
                "type_id": 0,
                "crush_weight": "0.099991",
                "depth": 1,
                "type": "osd",
                "id": 2
            },
            {
                "children": [
                    0
                ],
                "type": "host",
                "id": -30,
                "name": "vpm113ssd",
                "type_id": 1
            },
            {
                "status": "up",
                "name": "osd.0",
                "exists": 1,
                "reweight": "1.000000",
                "type_id": 0,
                "crush_weight": "0.099991",
                "depth": 1,
                "type": "osd",
                "id": 0
            },
            {
                "children": [
                    1
                ],
                "type": "host",
                "id": -20,
                "name": "vpm061ssd",
                "type_id": 1
            },
            {
                "status": "up",
                "name": "osd.1",
                "exists": 1,
                "reweight": "1.000000",
                "type_id": 0,
                "crush_weight": "0.099991",
                "depth": 1,
                "type": "osd",
                "id": 1
            },
            {
                "children": [
                    -5
                ],
                "type": "root",
                "id": -10,
                "name": "defaultssd",
                "type_id": 10
            },
            {
                "children": [
                    -4,
                    -3,
                    -2
                ],
                "type": "rack",
                "id": -5,
                "name": "rackthing",
                "type_id": 3
            },
            {
                "children": [
                    1
                ],
                "type": "host",
                "id": -2,
                "name": "vpm061",
                "type_id": 1
            },
            {
                "status": "up",
                "name": "osd.1",
                "exists": 1,
                "reweight": "1.000000",
                "type_id": 0,
                "crush_weight": "0.099991",
                "depth": 3,
                "type": "osd",
                "id": 1
            },
            {
                "children": [
                    0
                ],
                "type": "host",
                "id": -3,
                "name": "vpm113",
                "type_id": 1
            },
            {
                "status": "up",
                "name": "osd.0",
                "exists": 1,
                "reweight": "1.000000",
                "type_id": 0,
                "crush_weight": "0.099991",
                "depth": 3,
                "type": "osd",
                "id": 0
            },
            {
                "children": [
                    2
                ],
                "type": "host",
                "id": -4,
                "name": "vpm145",
                "type_id": 1
            },
            {
                "status": "up",
                "name": "osd.2",
                "exists": 1,
                "reweight": "1.000000",
                "type_id": 0,
                "crush_weight": "0.099991",
                "depth": 3,
                "type": "osd",
                "id": 2
            },
            {
                "children": [
                    -4,
                    -3,
                    -2
                ],
                "type": "root",
                "id": -1,
                "name": "default",
                "type_id": 10
            },
            {
                "children": [
                    1
                ],
                "type": "host",
                "id": -2,
                "name": "vpm061",
                "type_id": 1
            },
            {
                "status": "up",
                "name": "osd.1",
                "exists": 1,
                "reweight": "1.000000",
                "type_id": 0,
                "crush_weight": "0.099991",
                "depth": 2,
                "type": "osd",
                "id": 1
            },
            {
                "children": [
                    0
                ],
                "type": "host",
                "id": -3,
                "name": "vpm113",
                "type_id": 1
            },
            {
                "status": "up",
                "name": "osd.0",
                "exists": 1,
                "reweight": "1.000000",
                "type_id": 0,
                "crush_weight": "0.099991",
                "depth": 2,
                "type": "osd",
                "id": 0
            },
            {
                "children": [
                    2
                ],
                "type": "host",
                "id": -4,
                "name": "vpm145",
                "type_id": 1
            },
            {
                "status": "up",
                "name": "osd.2",
                "exists": 1,
                "reweight": "1.000000",
                "type_id": 0,
                "crush_weight": "0.099991",
                "depth": 2,
                "type": "osd",
                "id": 2
            }
        ]}}
        osd_map = OsdMap(None, self.osd_map_data)
        assert osd_map.parent_bucket_by_node_id == (
            {
                -5: [{'children': [-5],
                      'id': -10,
                      'name': 'defaultssd',
                      'type': 'root',
                      'type_id': 10
                      }],
                -4: [{'children': [-4, -3, -2],
                      'id': -5,
                      'name': 'rackthing',
                      'type': 'rack',
                      'type_id': 3
                      },
                     {'children': [-4, -3, -2],
                      'id': -1,
                      'name': 'default',
                      'type': 'root',
                      'type_id': 10
                      }],
                -3: [{'children': [-4, -3, -2],
                      'id': -5,
                      'name': 'rackthing',
                      'type': 'rack',
                      'type_id': 3
                      },
                     {'children': [-4, -3, -2],
                      'id': -1,
                      'name': 'default',
                      'type': 'root',
                      'type_id': 10
                      }],
                -2: [{'children': [-4, -3, -2],
                      'id': -5,
                      'name': 'rackthing',
                      'type': 'rack',
                      'type_id': 3
                      },
                     {'children': [-4, -3, -2],
                      'id': -1,
                      'name': 'default',
                      'type': 'root',
                      'type_id': 10
                      }],
                0: [{'children': [0],
                     'id': -30,
                     'name': 'vpm113ssd',
                     'type': 'host',
                     'type_id': 1
                     },
                    {'children': [0],
                     'id': -3,
                     'name': 'vpm113',
                     'type': 'host',
                     'type_id': 1
                     }],
                1: [{'children': [1],
                     'id': -20,
                     'name': 'vpm061ssd',
                     'type': 'host',
                     'type_id': 1
                     },
                    {'children': [1],
                     'id': -2,
                     'name': 'vpm061',
                     'type': 'host',
                     'type_id': 1
                     }],
                2: [{'children': [2],
                     'id': -40,
                     'name': 'vpm145ssd',
                     'type': 'host',
                     'type_id': 1
                     },
                    {'children': [2],
                     'id': -4,
                     'name': 'vpm145',
                     'type': 'host',
                     'type_id': 1
                     }]
            })

    def test_get_tree_node(self):
        osd_map = OsdMap(None, INTERESTING_OSD_MAP)
        assert osd_map.cmp(osd_map.get_tree_node(-1), (
            {
                'weight': 0.00012359535321593285,
                'alg': 'straw',
                'id': -1,
                'type_id': 6,
                'items': [{'pos': 0,
                           'weight': 2.7465634047985077e-05,
                           'id': -2
                           },
                          {'pos': 1,
                           'weight': 2.7465634047985077e-05,
                           'id': -3
                           },
                          {'pos': 2,
                           'weight': 2.7465634047985077e-05,
                           'id': -4
                           },
                          {'pos': 3,
                           'weight': 1.3732817023992538e-05,
                           'id': -5
                           },
                          {'pos': 4,
                           'weight': 1.3732817023992538e-05,
                           'id': -6
                           },
                          {'pos': 5,
                           'weight': 1.3732817023992538e-05,
                           'id': -7
                           }],
                'name': 'default',
                'type_name': 'root',
                'hash': 'rjenkins1'
            })) == 0
        with pytest.raises(Exception):
            osd_map.get_tree_node(10)


class TestCrushType(object):

    def test_shows_non_default_types(self):
        osd_map_data = MagicMock()
        data = {'crush': {'types': [{'type_id': 100, 'name': 'custom_type'}],
                          'buckets': []}}

        osd_map_data.__getitem__.side_effect = \
            lambda x: data[x] if x in data else osd_map_data
        osd_map = OsdMap(None, osd_map_data)
        assert {'type_id': 100, 'name': 'custom_type'} == \
            osd_map.crush_type_by_id[100]


class TestMonStatus(object):
    def test_mon_status(self):
        data = {}
        data['monmap'] = load_fixture("mon_map.json")
        mon_status = MonStatus(None, data)
        assert mon_status.mons_by_rank == (
            {
                0: {'name': 'gravel1',
                    'rank': 0,
                    'addr': '192.168.18.1:6789/0'
                    }
            })
        mon_status = MonStatus(None, None)
        assert mon_status.mons_by_rank == {}
