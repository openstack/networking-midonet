# Copyright 2017 Midokura SARL
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from os_vif import objects
from os_vif import plugin
from oslo_concurrency import processutils

from midonet.os_vif import linux_net
from midonet.os_vif import privsep


class MidoNetPlugin(plugin.PluginBase):

    def describe(self):
        return objects.host_info.HostPluginInfo(
            plugin_name="midonet",
            vif_info=[
                objects.host_info.HostVIFInfo(
                    vif_object_name=objects.vif.VIFGeneric.__name__,
                    min_version="1.0",
                    max_version="1.0"),
            ])

    def plug(self, vif, instance_info):
        """Perform operations to plug the VIF properly.

        :param vif: `os_vif.objects.vif.VIFBase` object.
        :param instance_info: `os_vif.objects.instance_info.InstanceInfo`
            object.
        :raises: `processutils.ProcessExecutionError`. Plugins implementing
                this method should let `processutils.ProcessExecutionError`
                bubble up.
        """

        # REVISIT(yamamoto): The above docstring can be removed once
        # https://review.openstack.org/#/c/577028/ is released.
        linux_net.create_tap_dev(vif.vif_name)
        _bind_port(vif.id, vif.vif_name)

    def unplug(self, vif, instance_info):
        """Perform operations to unplug the VIF properly.

        :param vif: `os_vif.objects.vif.VIFBase` object.
        :param instance_info: `os_vif.objects.instance_info.InstanceInfo`
            object.
        :raises: `processutils.ProcessExecutionError`. Plugins implementing
                this method should let `processutils.ProcessExecutionError`
                bubble up.
        """

        # REVISIT(yamamoto): The above docstring can be removed once
        # https://review.openstack.org/#/c/577028/ is released.
        _unbind_port(vif.id)
        linux_net.delete_net_dev(vif.vif_name)


@privsep.mm_ctl.entrypoint
def _bind_port(port_id, ifname):
    cmd = ('mm-ctl', '--bind-port', port_id, ifname)
    processutils.execute(*cmd)


@privsep.mm_ctl.entrypoint
def _unbind_port(port_id):
    cmd = ('mm-ctl', '--unbind-port', port_id)
    processutils.execute(*cmd)
