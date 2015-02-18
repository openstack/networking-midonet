# Copyright (c) 2015 Midokura Europe SARL, All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# This script generates RPM and debian packages.
#
# Usage: ./package.sh [-t] [VERSION_TAG]
#
#
#   -t: use timestamp based package name for unstable packges.
#
#   VERSION_TAG: Tag to determine version and revision string for
#                deb and RPM packages.
#                If ommited (recommended), it defaults to
#                `git describe --tags`
#

set -e

while getopts t OPT; do
    case "$OPT" in
      t)
          USE_TIMESTAMP=yes
          shift
          ;;
    esac
done

function set_timestamp_package_vals() {
    local version=$1

    pre_release_tag=$(date -u '+%Y%m%d%H%M').$(git rev-parse --short HEAD)

    rpm_version=$version
    rpm_revision="0".$pre_release_tag

    deb_version=$version~$pre_release_tag
    deb_revision=1
}


# Get version tag from command line or defaults to use git describe
version_tag=$1
if [ "$version_tag" == "" ]; then
    version_tag=$(git describe --tags)
fi

if [[ "$version_tag" =~ ^([0-9]{4}(\.[0-9]+){1,2})\+([0-9]+\.[0-9])$ ]]; then

    # For official release, e.g. 2014.2-1.0
    echo "Packaging official release: $version_tag"
    upstream_version=${BASH_REMATCH[1]}
    downstream_version=${BASH_REMATCH[3]}

    if [ "$USE_TIMESTAMP" == "yes" ]; then
        set_timestamp_package_vals $upstream_version+$downstream_version
    else
        rpm_version=$upstream_version+$downstream_version
        rpm_revision=1

        deb_version=$upstream_version+$downstream_version
        deb_revision=1
    fi

elif [[ "$version_tag" =~ ^([0-9]{4}(\.[0-9]+){1,2})\+([0-9]+\.[0-9])\.(rc[0-9]+)$ ]]; then
    # For RC packages, e.g. 2014.2-1.0-rc1
    echo "Producing RC packages for " $version_tag
    upstream_version=${BASH_REMATCH[1]}
    downstream_version=${BASH_REMATCH[3]}
    rc_tag=${BASH_REMATCH[4]}

    if [ "$USE_TIMESTAMP" == "yes" ]; then
        set_timestamp_package_vals $upstream_version+$downstream_version
    else
        rpm_version=$upstream_version+$downstream_version
        rpm_revision="0."$rc_tag

        deb_version=$upstream_version+$downstream_version~$rc_tag
        deb_revision=1
    fi

elif [[ "$version_tag" =~ ^([0-9]{4}(\.[0-9]+){1,2})\+([0-9]+\.[0-9])\.(rc[0-9]+.*)$ ]]; then
    # For unstable packages, e.g.2014.2-1.0-rc1-81-gef7115e
    echo Producing unstable packages for tag: $version_tag
    upstream_version=${BASH_REMATCH[1]}
    downstream_version=${BASH_REMATCH[3]}

    if [ "$USE_TIMESTAMP" == "yes" ]; then
        set_timestamp_package_vals $upstream_version+$downstream_version
    else
        pre_release_tag=$(echo ${BASH_REMATCH[4]} | sed -e 's/-/./g')

        rpm_version=$upstream_version+$downstream_version
        rpm_revision="0."$pre_release_tag

        deb_version=$upstream_version+$downstream_version~$pre_release_tag
        deb_revision=1
    fi

else
    echo "Aborted. invalid version tag. $version_tag"
    exit 1
fi


echo "Packaging with the following info"
echo "RPM: version=$rpm_version, revision=$rpm_revision"
echo "DEB: version=$deb_version, revision=$deb_revision"

# Common args for rpm and deb
FPM_BASE_ARGS=$(cat <<EOF
--architecture 'noarch' \
-d 'python-neutron' \
-d 'python-midonetclient' \
-s python
EOF
)

CFG=setup.cfg
CFG_BAK=setup.cfg.$version_tag

function create_cfg() {
    if [ -z "$1" ]; then
        echo "error: install location was not supplied"
        exit -1
    fi

    # Need to do this to have the files be installed in the right location
    cat > $CFG << EOF
# This is an auto-generated file from package.sh
[install]
install-lib=$1
install-scripts=/usr/bin
EOF
}

function package_rpm() {
    create_cfg /usr/lib/python2.7/site-packages

    local args=$(cat << EOF
--epoch 1
--version $rpm_version
--iteration $rpm_revision \
-t rpm
EOF
)
    eval fpm $FPM_BASE_ARGS $args setup.py
}

function package_deb() {
    create_cfg /usr/lib/python2.7/dist-packages

    local args=$(cat << EOF
--deb-priority 'optional' \
--version $deb_version \
--iteration $deb_revision \
-t deb
EOF
)
    eval fpm $FPM_BASE_ARGS $args setup.py
}

# Main
set +e

# Back up the config if exists
if [ -f $CFG ]; then
    echo "Backing up $CFG as $CFG_BAK"
    cp $CFG $CFG_BAK
fi

package_rpm
package_deb

# Restore the backed up config file
if [ -f $CFG_BAK ]; then
    echo "Restoring $CFG_BAK as $CFG"
    mv $CFG_BAK $CFG
fi
