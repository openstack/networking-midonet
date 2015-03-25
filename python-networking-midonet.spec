%global vendor MidoNet
%global srcname networking-midonet
%global docpath doc/build/html

Name:           python-%{srcname}		
Version:        2014.1.5+1.0
Release:	    <to-replace>
Provides:       python-%{srcname} = %{version}-%{release}
Summary:        %{vendor} OpenStack Neutron driver	

Group:          Applications/System
License:        ASL 2.0
URL:	        https://pypi.python.org/pypi/%{srcname}
Source0:	    https://pypi.python.org/packages/source/n/%{srcname}/%{srcname}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:	python2-devel
Requires:       python-neutron
Requires:	    python-babel
Requires:       python-pbr

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

%files
%license LICENSE
%{python2_sitelib}/midonet
%{python2_sitelib}/networking_midonet-%{version}-py%{python2_version}.egg-info
%{_bindir}/midonet-db-manage
