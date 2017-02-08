# This is the spec file for fallow

%define _topdir	 	%(echo $PWD)/
%define name		fallow 
%define version 	1.5
%define release		1
%define buildroot %{_topdir}/%{name}-%{version}-root

BuildRoot:	%{buildroot}
Summary: 		GNU fallow
License: 		GPL
Name: 			%{name}
Version: 		%{version}
Release: 		%{release}
Source: 		%{name}-%{version}.tar.gz
Prefix: 		/usr
Group: 			Grid Tools

%description
Fallow is used to drain slots in a multicore cluster.

%prep
%setup -q

%build

echo Nothing to do

%install
mkdir -p  $RPM_BUILD_ROOT
mkdir -p  $RPM_BUILD_ROOT/root/scripts
mkdir -p  $RPM_BUILD_ROOT/etc/init.d
cp fallow $RPM_BUILD_ROOT/etc/init.d
cp fallow.py $RPM_BUILD_ROOT/root/scripts
cp runFallow.sh $RPM_BUILD_ROOT/root/scripts
cp onlyMulticoreOff.sh $RPM_BUILD_ROOT/root/scripts
cp onlyMulticoreOn.sh  $RPM_BUILD_ROOT/root/scripts
cp onlyMulticoreShowAll.sh $RPM_BUILD_ROOT/root/scripts
cp onlyMulticoreShow.sh    $RPM_BUILD_ROOT/root/scripts

%post
chkconfig --add fallow
chkconfig fallow on

%files
%defattr(-,root,root)
/root/scripts/fallow.py
/root/scripts/fallow.pyo
/root/scripts/fallow.pyc
/root/scripts/runFallow.sh
/root/scripts/onlyMulticoreOff.sh
/root/scripts/onlyMulticoreOn.sh
/root/scripts/onlyMulticoreShowAll.sh
/root/scripts/onlyMulticoreShow.sh
/etc/init.d/fallow

