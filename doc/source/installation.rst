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

1. Install http://github.com/tendrl/common from the source code::

    $ git clone https://github.com/Tendrl/common.git
    $ cd common
    $ mkvirtualenv ceph-integration
    $ pip install .

2. Create common logging config file::

    $ cp etc/samples/logging.yaml.timedrotation.sample /etc/tendrl/ceph-integration_logging.yaml

Note that there are other sample config files for logging shipped with the product
and could be utilized for logging differently. For example there are config files
bundeled for syslog and journald logging as well. These could be used similarly as above.

3. Install ceph integration itself::

    $ git clone https://github.com/Tendrl/ceph-integration.git
    $ cd ceph-integration
    $ workon ceph-integration
    $ pip install .

Note that we use virtualenvwrapper_ here to activate ``ceph-integration`` `python
virtual enviroment`_. This way, we install *ceph integration* into the same virtual
enviroment which we have created during installation of *integration common*.

.. _virtualenvwrapper: https://virtualenvwrapper.readthedocs.io/en/latest/
.. _`python virtual enviroment`: https://virtualenv.pypa.io/en/stable/

4. Create config file::

    $ cp etc/tendrl/tendrl.conf.sample /etc/tendrl/tendrl.conf
    $ cp etc/logging.yaml.timedrotation.sample /etc/tendrl/ceph-integration_logging.yaml

5. Edit ``/etc/tendrl/tendrl.conf`` as below

    Set the value of ``log_cfg_path`` under section ``common``

    ``log_cfg_path = /etc/tendrl/common_logging.yaml``

    Set the value of ``log_cfg_path`` under section ``ceph-integration``

    ``log_cfg_path = /etc/tendrl/ceph-integration_logging.yaml``


6. Create log dir::

    $ mkdir /var/log/tendrl/common
    $ mkdir /var/log/tendrl/ceph-integration

7. Run::

    $ tendrl-ceph-integration

