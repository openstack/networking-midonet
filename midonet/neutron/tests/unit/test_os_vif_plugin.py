# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import mock
import testtools

from os_vif import objects
from oslo_concurrency import processutils

from midonet.os_vif import linux_net
from midonet.os_vif import privsep
from midonet.os_vif import vif_midonet


class PluginTest(testtools.TestCase):

    def setUp(self):
        super(PluginTest, self).setUp()
        privsep.mm_ctl.set_client_mode(False)

    def __init__(self, *args, **kwargs):
        super(PluginTest, self).__init__(*args, **kwargs)

        objects.register_all()

        self.subnet_bridge_4 = objects.subnet.Subnet(
            cidr='101.168.1.0/24',
            dns=['8.8.8.8'],
            gateway='101.168.1.1',
            dhcp_server='191.168.1.1')

        self.subnet_bridge_6 = objects.subnet.Subnet(
            cidr='101:1db9::/64',
            gateway='101:1db9::1')

        self.subnets = objects.subnet.SubnetList(
            objects=[self.subnet_bridge_4,
                     self.subnet_bridge_6])

        self.network = objects.network.Network(
            id='437c6db5-4e6f-4b43-b64b-ed6a11ee5ba7',
            subnets=self.subnets)

        self.vif = objects.vif.VIFGeneric(
            id='b679325f-ca89-4ee0-a8be-6db1409b69ea',
            address='ca:fe:de:ad:be:ef',
            network=self.network,
            vif_name='tap-xxx-yyy-zzz')

        self.instance = objects.instance_info.InstanceInfo(
            name='demo',
            uuid='f0000000-0000-0000-0000-000000000001')

    @mock.patch.object(linux_net, 'create_tap_dev')
    @mock.patch.object(processutils, 'execute')
    def test_plug(self, execute, create_tap_dev):
        plugin = vif_midonet.MidoNetPlugin.load("midonet")
        plugin.plug(self.vif, self.instance)
        create_tap_dev.assert_called_once_with('tap-xxx-yyy-zzz')
        execute.assert_called_once_with(
            'mm-ctl', '--bind-port',
            'b679325f-ca89-4ee0-a8be-6db1409b69ea', 'tap-xxx-yyy-zzz')

    @mock.patch.object(linux_net, 'delete_net_dev')
    @mock.patch.object(processutils, 'execute')
    def test_unplug(self, execute, delete_net_dev):
        plugin = vif_midonet.MidoNetPlugin.load("midonet")
        plugin.unplug(self.vif, self.instance)
        delete_net_dev.assert_called_once_with('tap-xxx-yyy-zzz')
        execute.assert_called_once_with(
            'mm-ctl', '--unbind-port', 'b679325f-ca89-4ee0-a8be-6db1409b69ea')
