from mock import MagicMock
import pytest
import sys
sys.modules['tendrl.ceph_bridge.config'] = MagicMock()
sys.modules['logging'] = MagicMock()
from tendrl.ceph_bridge.persistence import persister
del sys.modules['tendrl.ceph_bridge.config']
del sys.modules['logging']


class Test_deferred_call(object):
    def setup_method(self, method):
        self.fn = MagicMock()
        self.deferred_call = persister.deferred_call(
            self.fn, ["pytest"], {"test": "pytest"}
            )

    def test_deferred_call(self):
        self.deferred_call.call_it()
        self.deferred_call.fn.assert_called_with(
            "pytest", test="pytest"
            )


class Test_Persister(object):
    def setup_method(self, method):
        persister.etcd_server = MagicMock()
        self.Persister = persister.Persister()

    def test_Persister_Creation(self):
        assert self.Persister is not None

    def test_getattribute_(self):
        """Check __getattribute__ with dummy function"""
        with pytest.raises(AttributeError):
            self.Persister.test_func()
        """Check __getattribute__ raise excption for variable"""
        self.Persister._testing = None
        with pytest.raises(AttributeError):
            self.Persister.testing()
        persister.deferred_call = MagicMock(return_value=None)
        with pytest.raises(Exception):
            self.Persister.create_server()

    def test_update_sync_object(self):
        """Sending dummy parameters"""
        data = "data"
        updated = "updated"
        fsid = "fsid"
        name = "name"
        sync_type = "sync_type"
        version = "version"
        when = "when"
        self.Persister._update_sync_object(
            updated, fsid, name, sync_type, version, when, data)
        self.Persister._store.save.assert_called()

    def test_create_server(self):
        self.Persister._create_server("servers")
        self.Persister._store.save.assert_called_with(
            "servers"
            )

    def test_create_service(self):
        self.Persister._create_service("service")
        self.Persister._store.save.assert_called_with(
            "service"
            )

    def test_save_events(self):
        self.Persister._save_events(["Event1", "Event2"])
        self.Persister._store.save.assert_called_with(
            "Event2"
            )

    def test_run(self, monkeypatch):
        def stop_while_loop(temp):
            self.Persister.stop()
        assert self.Persister._complete.is_set() is False
        monkeypatch.setattr(persister.gevent, 'sleep', stop_while_loop)
        self.Persister._run()
        assert self.Persister._complete.is_set() is True
