#! /bin/sh

# Copyright (C) 2016 Midokura SARL.
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

set -x
set -e

TMPDIR=`mktemp -d /tmp/${0##*/}.XXXXXX` || exit 1
trap "rm -rf ${TMPDIR}" EXIT

EGG_DIR=networking_midonet.egg-info

rm -rf ${EGG_DIR}
SKIP_GIT_SDIST=1 python ./setup.py egg_info
sort ${EGG_DIR}/SOURCES.txt > ${TMPDIR}/without_git

rm -rf ${EGG_DIR}
SKIP_GIT_SDIST=0 python ./setup.py egg_info
sort ${EGG_DIR}/SOURCES.txt > ${TMPDIR}/with_git

diff -upd ${TMPDIR}/with_git ${TMPDIR}/without_git
