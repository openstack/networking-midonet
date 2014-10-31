# Get version number from command line
#
# This script generates RPM and debian packages.
#
# Usage: ./package.sh [VERSION_TAG]
#
#   VERSION_TAG: Tag to determine version and revision string for
#                deb and RPM packages.
#                If ommited (recommended), it defaults to
#                `git describe --tags`
#

set -e

# Get version tag from command line or defaults to use git describe
version_tag=$1
if [ "$version_tag" == "" ]; then
    version_tag=$(git describe --tags)
fi

if [[ "$version_tag" =~ ^([0-9]{4}\.[0-9]+)-([0-9]+\.[0-9])$ ]]; then

    # For official release, e.g. 2014.2-1.0
    echo "Packaging official release: $version_tag"
    upstream_version=${BASH_REMATCH[1]}
    downstream_version=${BASH_REMATCH[2]}

    rpm_version=$upstream_version-$downstream_version
    rpm_revision=1.0

    deb_version=$upstream_version-$downstream_version

elif [[ "$version_tag" =~ ^([0-9]{4}\.[0-9]+)-([0-9]+\.[0-9])-(rc[0-9]+)$ ]]; then
    # For RC packages, e.g. 2014.2-1.0-rc1
    echo "Producing RC packages for " $version_tag
    upstream_version=${BASH_REMATCH[1]}
    downstream_version=${BASH_REMATCH[2]}
    rc_tag=${BASH_REMATCH[3]}

    rpm_version=$upstream_version-$downstream_version
    rpm_revision=$rc_tag

    deb_version=$upstream_version-$downstream_version~$rc_tag

elif [[ "$version_tag" =~ ^([0-9]{4}\.[0-9]+)-([0-9]+\.[0-9])-(rc[0-9]+.*)$ ]]; then
    # For unstable packages, e.g.2014.2-1.0-rc1-81-gef7115e
    echo Producing unstable packages for tag: $version_tag
    upstream_version=${BASH_REMATCH[1]}
    downstream_version=${BASH_REMATCH[2]}
    pre_release_tag=$(echo ${BASH_REMATCH[3]} | sed -e 's/-/./g')

    rpm_version=$upstream_version-$downstream_version
    rpm_revision=$pre_release_tag

    deb_version=$upstream_version-$downstream_version~$pre_release_tag

else
    echo "Aborted. invalid version tag. $version_tag"
    exit 1
fi


echo "Packaging with the following info"
echo "RPM: version=$rpm_version, revision=$rpm_revision"
echo "DEB: version=$deb_version"


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
-s dir
EOF
)


function clean() {
    rm -rf build
}

RPM_ARGS=$(cat <<EOF
-d 'python >= 2.6' -d 'python < 2.8' \
--epoch 1
--version $rpm_version
--iteration $rpm_revision
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
--version $deb_version
EOF
)
function package_deb() {
    eval fpm $FPM_BASE_ARGS $DEB_ARGS -t deb .
}


# Main
clean
package_rpm
package_deb
