# Copyright 2012 OpenStack Foundation
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

import mock
from oslo_utils import uuidutils

from neutron.agent.linux import utils
from neutron.conf.agent import common as config
from neutron.tests.unit.agent.linux import test_interface as n_test

from midonet.neutron.agent import interface


class TestMidonetInterfaceDriver(n_test.TestBase):
    def setUp(self):
        self.conf = config.setup_conf()
        config.register_interface_opts(self.conf)
        self.driver = interface.MidonetInterfaceDriver(self.conf)
        self.network_id = uuidutils.generate_uuid()
        self.port_id = uuidutils.generate_uuid()
        self.device_name = "tap0"
        self.mac_address = "aa:bb:cc:dd:ee:ff"
        self.bridge = "br-test"
        self.namespace = "ns-test"
        super(TestMidonetInterfaceDriver, self).setUp()

    def test_plug(self):
        cmd = ['mm-ctl', '--bind-port', self.port_id, 'tap0']
        self.device_exists.return_value = False

        root_dev = mock.Mock()
        ns_dev = mock.Mock()
        self.ip().add_veth = mock.Mock(return_value=(root_dev, ns_dev))
        with mock.patch.object(utils, 'execute') as execute:
            self.driver.plug(
                self.network_id, self.port_id,
                self.device_name, self.mac_address,
                self.bridge, self.namespace)
            execute.assert_called_once_with(cmd, run_as_root=True)

        expected = [mock.call(), mock.call(),
                    mock.call().add_veth(self.device_name,
                                         self.device_name,
                                         namespace2=self.namespace)]

        ns_dev.assert_has_calls(
            [mock.call.link.set_address(self.mac_address)])

        root_dev.assert_has_calls(
            [mock.call.disable_ipv6(), mock.call.link.set_up()])
        ns_dev.assert_has_calls([mock.call.link.set_up()])
        self.ip.assert_has_calls(expected, True)

    def test_unplug(self):
        self.driver.unplug(self.device_name, self.bridge, self.namespace)

        self.ip_dev.assert_has_calls([
            mock.call(self.device_name, namespace=self.namespace),
            mock.call().link.delete()])
        self.ip.assert_has_calls([mock.call().garbage_collect_namespace()])
