# Copyright (c) 2015 Midokura SARL
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

from oslo_log import log as logging

from neutron_lib import constants as n_const

from neutron.agent.linux import interface as n_interface
from neutron.agent.linux import ip_lib
from neutron.agent.linux import utils

LOG = logging.getLogger(__name__)


class MidonetInterfaceDriver(n_interface.LinuxInterfaceDriver):

    def plug_new(self, network_id, port_id, device_name, mac_address,
                 bridge=None, namespace=None, prefix=None, mtu=None):
        """Plug an interface.

        This method is called by the Dhcp agent or by the L3 agent
        when a new network is created
        """
        ip = ip_lib.IPWrapper()
        tap_name = device_name.replace(prefix or n_const.TAP_DEVICE_PREFIX,
                                       n_const.TAP_DEVICE_PREFIX)

        # Create ns_dev in a namespace if one is configured.
        root_dev, ns_dev = ip.add_veth(tap_name, device_name,
                                       namespace2=namespace)
        root_dev.disable_ipv6()
        ns_dev.link.set_address(mac_address)

        if mtu:
            ns_dev.link.set_mtu(mtu)
            root_dev.link.set_mtu(mtu)
        else:
            LOG.warning("No MTU configured for port %s", port_id)

        ns_dev.link.set_up()
        root_dev.link.set_up()

        cmd = ['mm-ctl', '--bind-port', port_id, device_name]
        utils.execute(cmd, run_as_root=True)  # nosec

    def unplug(self, device_name, bridge=None, namespace=None, prefix=None):
        # the port will be deleted by the dhcp agent that will call the plugin
        device = ip_lib.IPDevice(device_name, namespace=namespace)
        try:
            device.link.delete()
        except RuntimeError:
            LOG.error("Failed unplugging interface '%s'", device_name)
        LOG.debug("Unplugged interface '%s'", device_name)

        ip_lib.IPWrapper(namespace=namespace).garbage_collect_namespace()
