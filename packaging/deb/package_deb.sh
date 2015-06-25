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

# Define the packager
export DEBFULLNAME='Jaume Devesa'
export DEBEMAIL='jaume@midokura.com'

# Create the target directory where the rpm will be copied
SCRIPT_DIR="$( cd "$(dirname "${BASH_SOURCE[0]}" )" && pwd )"
SOURCE_DIR="$( cd "$SCRIPT_DIR" && cd ../../ && pwd )"
TARGET_DIR=${SOURCE_DIR}/DEBS
mkdir -p $TARGET_DIR

cd $SOURCE_DIR

# Get the version from sources
VERSION=`cat setup.cfg | grep version | grep -o '[0-9.]*'`

# Create the source distribution and untar it
python setup.py sdist --dist-dir /tmp
tar xzvf /tmp/networking-midonet-${VERSION}.tar.gz -C /tmp

# Replace the version and release depending on the version tag
# This command will check if we live in a tag commit or not
version_tag=$(git describe --candidates 0)

# If the command fails, we are in a SNAPSHOT commit
if [ $? -ne 0 ]; then
    # Determine the nightly build
    DATE=`date +%Y%m%d`
    SHA=`git log --pretty=format:'%h' -n 1`
    SNAPSHOT="${DATE}git${SHA}"
    FULL_VERSION=${VERSION}~${SNAPSHOT}
else
  if [[ "$version_tag" =~ ^[0-9]{4}(\.[0-9]+){4}$ ]]; then
    # Final version tag (no rc)
    echo "Final version ${BASH_REMATCH[0]}"
    if [[ "${BASH_REMATCH[0]}" != $VERSION ]]; then
        echo "Tag version '${BASH_REMATCH[0]}' and source version '$VERSION' mismatch"
        exit 2;
    fi
    FULL_VERSION=${VERSION}

  elif [[ "$version_tag" =~ ^([0-9]{4}(\.[0-9]+){4})-(rc[0-9]+)$ ]]; then
    # release candidate
    echo "Version ${BASH_REMATCH[1]}"
    echo "Release candidate version ${BASH_REMATCH[3]}"
    if [[ "${BASH_REMATCH[1]}" != $VERSION ]]; then
        echo "Tag version '${BASH_REMATCH[1]}' and source version '$VERSION' mismatch"
        exit 2;
    fi
    FULL_VERSION=${VERSION}~${BASH_REMATCH[3]}
  else
    echo "Invalid version tag $version_tag"
    exit 1;
  fi
fi

# Change the name of the tar as debian packager expects to see
mv /tmp/networking-midonet-${VERSION}.tar.gz /tmp/networking-midonet_${FULL_VERSION}.orig.tar.gz

# Copy the packaging debian commands into extracted dir to build the deb
cp -r ${SOURCE_DIR}/packaging/deb/debian /tmp/networking-midonet-${VERSION}

# Generate the 'changelog' file via 'dhc' based on current version
cd /tmp/networking-midonet-${VERSION}
dch --create -v 1:${FULL_VERSION} --package networking-midonet "Release 1:${FULL_VERSION}"

debuild -us -uc

cp /tmp/*.deb $TARGET_DIR
