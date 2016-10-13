===========
Environment
===========

1. Install Ceph (http://docs.ceph.com/docs/jewel/start/)
2. Install Etcd>=2.3.x && <3.x (https://github.com/coreos/etcd/releases/tag/v2.3.7)


============
Installation
============

Since there is no stable release yet, the only option is to install the project
from the source.

Development version from the source
-----------------------------------

1. Install http://github.com/tendrl/bridge_common from the source code::

    $ git clone https://github.com/Tendrl/bridge_common.git
    $ cd bridge_common
    $ mkvirtualenv ceph_bridge
    $ pip install .

2. Install ceph bridge itself::

    $ git clone https://github.com/Tendrl/ceph_bridge.git
    $ cd ceph_bridge
    $ workon ceph_bridge
    $ pip install .

Note that we use virtualenvwrapper_ here to activate ``ceph_bridge`` `python
virtual enviroment`_. This way, we install *ceph bridge* into the same virtual
enviroment which we have created during installation of *bridge common*.

.. _virtualenvwrapper: https://virtualenvwrapper.readthedocs.io/en/latest/
.. _`python virtual enviroment`: https://virtualenv.pypa.io/en/stable/

3. Create config file::

    $ cp etc/tendrl/tendrl.conf.sample /etc/tendrl/tendrl.conf

4. Edit ``/etc/tendrl/tendrl.conf`` as required

5. Create log dir::

    $ mkdir /var/log/tendrl

6. Run::

    $ tendrl-ceph-bridge
