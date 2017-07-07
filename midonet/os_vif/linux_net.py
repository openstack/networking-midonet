# Derived from:
#   nova/network/linux_net.py
#   vif_plug_ovs/linux_net.py
#
# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
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

import os

from oslo_concurrency import processutils
from oslo_log import log as logging
from oslo_utils import excutils

from midonet.os_vif import privsep


LOG = logging.getLogger(__name__)


def execute(*cmd, **kwargs):
    return processutils.execute(*cmd, **kwargs)


def device_exists(device):
    """Check if ethernet device exists."""
    return os.path.exists('/sys/class/net/%s' % device)


@privsep.vif_plug.entrypoint
def create_tap_dev(dev, mac_address=None, multiqueue=False):
    if not device_exists(dev):
        try:
            # First, try with 'ip'
            cmd = ('ip', 'tuntap', 'add', dev, 'mode', 'tap')
            if multiqueue:
                cmd = cmd + ('multi_queue', )
            execute(*cmd, check_exit_code=[0, 2, 254])
        except processutils.ProcessExecutionError:
            if multiqueue:
                LOG.warning(
                    'Failed to create a tap device with ip tuntap. '
                    'tunctl does not support creation of multi-queue '
                    'enabled devices, skipping fallback.')
                raise

            # Second option: tunctl
            execute('tunctl', '-b', '-t', dev)
        if mac_address:
            execute('ip', 'link', 'set', dev, 'address', mac_address,
                    check_exit_code=[0, 2, 254])
        execute('ip', 'link', 'set', dev, 'up', check_exit_code=[0, 2, 254])


@privsep.vif_plug.entrypoint
def delete_net_dev(dev):
    """Delete a network device only if it exists."""
    if device_exists(dev):
        try:
            execute('ip', 'link', 'delete', dev, check_exit_code=[0, 2, 254])
            LOG.debug("Net device removed: '%s'", dev)
        except processutils.ProcessExecutionError:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed removing net device: '%s'", dev)
