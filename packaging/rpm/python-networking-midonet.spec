%global vendor  MidoNet
%global srcname networking-midonet
%global pkgname python-neutron-plugin-midonet
%global docpath doc/build/html

%if 0%{?rhel} && 0%{?rhel} <= 6
%{!?__python2: %global __python2 /usr/bin/python2}
%{!?python2_sitelib: %global python2_sitelib %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python2_version: %global python2_version %(%{__python2} -c "from distutils.sysconfig import get_python_version; print(get_python_version())")}
%{!?python2_sitearch: %global python2_sitearch %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

%if 0%{?el7}
%define dist .el7
%endif

Name:           %{pkgname}
Version:        XXX
Release:        XXX%{?dist}
Epoch:          1
Provides:       %{pkgname} = %{version}-%{release}
Summary:        %{vendor} OpenStack Neutron driver

Group:          Applications/System
License:        ASL 2.0
URL:            https://pypi.python.org/pypi/%{srcname}
Source0:        %{srcname}-%{version}.tar.gz

BuildArch:      noarch
BuildRoot:      %{_topdir}/BUILDROOT/
BuildRequires:  python2-devel
BuildRequires:  python-setuptools
Requires:       python-neutron
Requires:       python-midonetclient

%description
This package provides %{vendor} networking driver for OpenStack Neutron

%prep
%setup -q -n %{srcname}-%{version}

%build
rm requirements.txt test-requirements.txt
%{__python2} setup.py build

%install
export PBR_VERSION=%{version}
export SKIP_PIP_INSTALL=1
%{__python2} setup.py install --skip-build --root $RPM_BUILD_ROOT

%clean
rm -rf %{buildroot}

%files
%attr(-, root, root) %doc LICENSE
%attr(-, root, root) %{python2_sitelib}/midonet
%attr(-, root, root) %{python2_sitelib}/networking_midonet-%{version}-py%{python2_version}.egg-info
