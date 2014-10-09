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
--version $pkgver
EOF
)


function clean() {
    rm -rf build
}

RPM_ARGS=$(cat <<EOF
-d 'python >= 2.6' -d 'python < 2.8' \
--epoch 1
EOF
)
function package_rpm() {
    RPM_BUILD_DIR=build/rpm/
    mkdir -p  $RPM_BUILD_DIR/usr/lib/python2.6/site-packages/
    mkdir -p  $RPM_BUILD_DIR/usr/lib/python2.7/site-packages/

    cp -r midonet $RPM_BUILD_DIR/usr/lib/python2.6/site-packages/
    cp -r midonet $RPM_BUILD_DIR/usr/lib/python2.7/site-packages/

    eval fpm $FPM_BASE_ARGS $RPM_ARGS -C $RPM_BUILD_DIR -t rpm .
}


DEB_ARGS=$(cat <<EOF
--prefix /usr/lib/python2.7/dist-packages/midonet \
--deb-priority 'optional' \
-C midonet/
EOF
)
function package_deb() {
    eval fpm $FPM_BASE_ARGS $DEB_ARGS -t deb .
}


# Main
clean
package_rpm
package_deb
