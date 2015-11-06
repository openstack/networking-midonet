#!/bin/sh

# Many of neutron's repos suffer from the problem of depending on neutron,
# but it not existing on pypi.

# This wrapper for tox's package installer will use the existing package
# if it exists, else use zuul-cloner if that program exists, else grab it
# from neutron master via a hard-coded URL. That last case should only
# happen with devs running unit tests locally.

# From the tox.ini config page:
# install_command=ARGV
# default:
# pip install {opts} {packages}

PROJ=$1
shift 1

ZUUL_CLONER=/usr/zuul-env/bin/zuul-cloner
neutron_installed=$(echo "import ${PROJ}" | python 2>/dev/null ; echo $?)

set -e

if [ $neutron_installed -eq 0 ]; then
    echo "ALREADY INSTALLED" > /tmp/tox_install.txt
    echo "Neutron already installed; using existing package"
elif [ -x "$ZUUL_CLONER" ]; then
    echo "ZUUL CLONER" > /tmp/tox_install.txt
    cwd=$(/bin/pwd)
    cd /tmp
    $ZUUL_CLONER --cache-dir \
        /opt/git \
        git://git.openstack.org \
        openstack/${PROJ}
    cd openstack/${PROJ}
    pip install -e .
    cd "$cwd"
else
    echo "PIP HARDCODE" > /tmp/tox_install.txt
    pip install -U -egit+https://git.openstack.org/openstack/${PROJ}@stable/liberty#egg=${PROJ}
fi

pip install -U $*
exit $?
