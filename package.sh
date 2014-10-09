# Get version number from command line
#
# This script generates RPM and debian packages.
#
# Usage: ./package.sh [VERSION_STRING]
#
#   VERSION_STRING: version string for deb and RPM packaes.
#                   If ommited (recommended), it defaults to
#                   `git describe --tag | sed 's/^v//'`
#

set -e

# Get version number from command line or defaults to use git describe
pkgver=$1
if [ "$pkgver" == "" ]; then
    pkgver=$(git describe --tag | sed 's/^v//')
fi
echo "Packaging with version number $pkgver"

# Common args for rpm and deb
FPM_BASE_ARGS=$(cat <<EOF
--name 'python-neutron-plugin-midonet' \
--architecture 'noarch' \
--license '2014, Midokura' \
--vendor 'Midokura' \
--maintainer "Midokura" \
--url 'http://midokura.com' \
--description 'Neutron is a virtual network service for Openstack - Python library
  Neutron MidoNet plugin is a MidoNet virtual network service plugin for Openstack Neutron.' \
-d 'python-neutron' \
-d 'python-midonetclient' \
-s dir \
-C midonet/ \
--version $pkgver
EOF
)

RPM_ARGS=$(cat <<EOF
--prefix /usr/lib/python2.6/site-packages/midonet \
--epoch 1
EOF
)

DEB_ARGS=$(cat <<EOF
--prefix /usr/lib/python2.7/dist-packages/midonet \
--deb-priority 'optional'
EOF
)

# Package rpm
eval fpm $FPM_BASE_ARGS $RPM_ARGS -t rpm .

# Package debian
eval fpm $FPM_BASE_ARGS $DEB_ARGS -t deb .
