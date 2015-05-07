#!/bin/bash
# Copyright (C) 2015 Midokura SARL.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# Create the rpm packages for the current code. It is based on **annotated**
# tags:
#
# * If the current commit does not belong to a tag, we create a snapshot
#   package with the format:
#       python-networking-midonet-2015.1.0.1.0-0.0.20150434git238ab24.noarch.rpm
#
# * If this commit is a tag commit and belongs to a release candidate tag:
#       python-networking-midonet-2015.1.2.2.0-0.1.rc4.noarch.rpm
#
# * If this commit is a tag and is a release tag (no 'rc'), it builds the release
#   package:
#
#       python-networking-midonet-2015.2.0.1.1-1.noarch.rpm
#
# Tag version number must match with the `version` tag of the setup.cfg

set -x

# Create snapshot package
function snapshot {
    # Determine the nightly build
    DATE=`date +%Y%m%d`
    SHA=`git log --pretty=format:'%h' -n 1`

    # Replace the spec file with the given snapshot value
    sed -ie "s/Version:\s\+XXX/Version:        ${VERSION}/" $HOME/rpmbuild/SPECS/python-networking-midonet.spec
    sed -ie "s/Release:\s\+XXX/Release:        0.0.${DATE}git${SHA}/" $HOME/rpmbuild/SPECS/python-networking-midonet.spec
    echo "Building ptyhon-neutron-plugin-midonet package for snapshot ${DATE}git${SHA}"
}

function rc {
    # Get the values to build the rc package
    RC=$1

    # Replace the spec file with the given snapshot value
    sed -ie "s/Version:\s\+XXX/Version:        ${VERSION}/" $HOME/rpmbuild/SPECS/python-networking-midonet.spec
    sed -ie "s/Release:\s\+XXX/Release:        0.1.${RC}/" $HOME/rpmbuild/SPECS/python-networking-midonet.spec
    echo "Building ptyhon-neutron-plugin-midonet package for release candidate ${RC}"
}

function release {
    # Replace the spec file with the given snapshot value
    sed -ie "s/Version:\s\+XXX/Version:        ${VERSION}/" $HOME/rpmbuild/SPECS/python-networking-midonet.spec
    sed -ie "s/Release:\s\+XXX/Release:        1/" $HOME/rpmbuild/SPECS/python-networking-midonet.spec
    echo "Building ptyhon-neutron-plugin-midonet package for release ${VERSION}"
}

# Create the target directory where the rpm will be copied
SCRIPT_DIR="$( cd "$(dirname "${BASH_SOURCE[0]}" )" && pwd )"
SOURCE_DIR=$SCRIPT_DIR/../..
TARGET_DIR=$SOURCE_DIR/RPMS
mkdir -p $TARGET_DIR

# Make sure we are in the source code directory
cd $SOURCE_DIR

# Create the structure of directories to build the rpm
# a new hierarchy will be created in $HOME/rpmbuild
rm -rf $HOME/rpmbuild
rpmdev-setuptree

# Create the tarball into the SOURCES directory
python setup.py sdist --dist-dir $HOME/rpmbuild/SOURCES

# Move the spec file to the SPECS directory (Version: and Release: to be replaced)
cp packaging/rpm/python-networking-midonet.spec $HOME/rpmbuild/SPECS

# Get the version from sources
VERSION=$(cat setup.cfg | grep version | grep -o '[0-9.]*')

# Replace the version and release depending on the version tag
# This command will check if we live in a tag commit or not
version_tag=$(git describe --candidates 0)

# If the command fails, we are in a SNAPSHOT commit
if [ $? -ne 0 ]; then
  snapshot
else
  if [[ "$version_tag" =~ ^[0-9]{4}(\.[0-9]+){2}$ ]]; then
    # Final version tag (no rc)
    echo "Final version ${BASH_REMATCH[0]}"
    if [[ "${BASH_REMATCH[0]}" != $VERSION ]]; then
        echo "Tag version '${BASH_REMATCH[0]}' and source version '$VERSION' mismatch"
        exit 2;
    fi
    release

  elif [[ "$version_tag" =~ ^([0-9]{4}(\.[0-9]+){2})-(rc[0-9]+)$ ]]; then
    # release candidate
    echo "Version ${BASH_REMATCH[1]}"
    echo "Release candidate version ${BASH_REMATCH[3]}"
    if [[ "${BASH_REMATCH[1]}" != $VERSION ]]; then
        echo "Tag version '${BASH_REMATCH[1]}' and source version '$VERSION' mismatch"
        exit 2;
    fi
    rc ${BASH_REMATCH[3]}

  else
    echo "Invalid version tag $version_tag"
    exit 1;
  fi
fi

rpmbuild -ba $HOME/rpmbuild/SPECS/python-networking-midonet.spec

cp -r $HOME/rpmbuild/RPMS/noarch/*.rpm $TARGET_DIR
