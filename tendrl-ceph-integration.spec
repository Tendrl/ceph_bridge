Name: tendrl-ceph-integration
Version: 1.2
Release: 1%{?dist}
BuildArch: noarch
Summary: Tendrl bridge for Ceph Storage
Source0: %{name}-%{version}.tar.gz
License: LGPLv2+
URL: https://github.com/Tendrl/ceph-integration

BuildRequires: python2-devel
BuildRequires: pytest
BuildRequires: systemd

Requires: python-etcd
Requires: python-gevent
Requires: python-greenlet
Requires: pytz
Requires: python-msgpack
Requires: tendrl-commons

%description
Tendrl bridge for Ceph Storage

%prep
%setup

# Remove bundled egg-info
rm -rf %{name}.egg-info

%build
%{__python} setup.py build

%install
%{__python} setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
install -m  0755  --directory $RPM_BUILD_ROOT%{_sysconfdir}/tendrl/ceph-integration
install -m  0755 --directory $RPM_BUILD_ROOT%{_var}/log/tendrl/ceph-integration
install -m  0755  --directory $RPM_BUILD_ROOT%{_datadir}/tendrl/ceph-integration
install -Dm 0644  etc/tendrl/ceph-integration/ceph-integration.conf.yaml.sample $RPM_BUILD_ROOT%{_sysconfdir}/tendrl/ceph-integration/ceph-integration.conf.yaml
install -Dm 0644  etc/tendrl/ceph-integration/*.yaml.* $RPM_BUILD_ROOT%{_datadir}/tendrl/ceph-integration/.
install -Dm 0644 etc/tendrl/ceph-integration/logging.yaml.timedrotation.sample $RPM_BUILD_ROOT%{_sysconfdir}/tendrl/ceph-integration/ceph-integration_logging.yaml
install -p -D -m 0644 systemd/tendrl-cephd.service $RPM_BUILD_ROOT%{_unitdir}/tendrl-cephd.service

%post
%systemd_post tendrl-cephd.service

%preun
%systemd_preun tendrl-cephd.service

%postun
%systemd_postun_with_restart tendrl-cephd.service

%check
py.test -v tendrl/ceph_integration/tests || :

%files -f INSTALLED_FILES
%dir %{_var}/log/tendrl/ceph-integration
%dir %{_sysconfdir}/tendrl/ceph-integration
%doc README.rst
%license LICENSE
%{_datadir}/tendrl/ceph-integration/.
%{_unitdir}/tendrl-cephd.service
%{_sysconfdir}/tendrl/ceph-integration/ceph-integration_logging.yaml
%{_sysconfdir}/tendrl/ceph-integration/ceph-integration.conf.yaml

%changelog
* Mon Jan 23 2017 Timothy Asir Jeyasingh <tjeyasin@redhat.com> - 1.1-1
- Config file changes
- Import ceph

* Wed Oct 26 2016 Timothy Asir Jeyasingh <tjeyasin@redhat.com> - 0.0.1-1
- Initial build.
