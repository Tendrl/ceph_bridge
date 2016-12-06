Name: tendrl-ceph-integration
Version: 1.1
Release: 1%{?dist}
BuildArch: noarch
Summary: Tendrl bridge for Ceph Storage
Source0: %{name}-%{version}.tar.gz
License: LGPLv2+
URL: https://github.com/Tendrl/ceph_integration

BuildRequires: python2-devel
BuildRequires: pytest
BuildRequires: systemd

Requires: python-etcd
Requires: python-dateutil
Requires: python-gevent
Requires: python-greenlet
Requires: pytz
Requires: python-msgpack
Requires: tendrl-common

%description
Tendrl bridge for Ceph Storage

%prep
%setup
# Remove the requirements file to avoid adding into
# distutils requiers_dist config
rm -rf {test-,}requirements.txt

# Remove bundled egg-info
rm -rf %{name}.egg-info

%build
%{__python} setup.py build

%install
%{__python} setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
install -m  0755 --directory $RPM_BUILD_ROOT%{_var}/log/tendrl/ceph_integration
install -m  0755  --directory $RPM_BUILD_ROOT%{_sysconfdir}/tendrl/ceph_integration
install -m  0755  --directory $RPM_BUILD_ROOT%{_datadir}/tendrl/ceph_integration
install -p -D -m 0644 systemd/tendrl-cephd.service $RPM_BUILD_ROOT%{_unitdir}/tendrl-cephd.service
install -Dm 0644 etc/logging.yaml.timedrotation.sample $RPM_BUILD_ROOT%{_sysconfdir}/tendrl/ceph_integration_logging.yaml
install -Dm 644 etc/*.sample $RPM_BUILD_ROOT%{_datadir}/tendrl/ceph_integration/.

%post
%systemd_post tendrl-cephd.service

%preun
%systemd_preun tendrl-cephd.service

%postun
%systemd_postun_with_restart tendrl-cephd.service

%check
py.test -v tendrl/ceph_integration/tests || :

%files -f INSTALLED_FILES
%dir %{_var}/log/tendrl/ceph_integration
%dir %{_sysconfdir}/tendrl/ceph_integration
%dir %{_datadir}/tendrl/ceph_integration
%doc README.rst
%license LICENSE
%{_datadir}/tendrl/ceph_integration/
%{_unitdir}/tendrl-cephd.service
%{_sysconfdir}/tendrl/ceph_integration_logging.yaml

%changelog
* Wed Oct 26 2016 Timothy Asir Jeyasingh <tjeyasin@redhat.com> - 0.0.1-1
- Initial build.
