#! /bin/sh

set -e

DIR=$(dirname $0)
${DIR}/tox_install_project.sh neutron neutron $*
${DIR}/tox_install_project.sh neutron-fwaas neutron_fwaas $*
${DIR}/tox_install_project.sh neutron-lbaas neutron_lbaas $*
${DIR}/tox_install_project.sh neutron-vpnaas neutron_vpnaas $*
