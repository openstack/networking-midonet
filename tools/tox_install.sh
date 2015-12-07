#! /bin/sh

set -e

DIR=$(dirname $0)
${DIR}/tox_install_project.sh neutron $*
${DIR}/tox_install_project.sh neutron-fwaas $*
${DIR}/tox_install_project.sh neutron-lbaas $*
${DIR}/tox_install_project.sh neutron-vpnaas $*
