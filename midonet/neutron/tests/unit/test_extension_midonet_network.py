# Copyright 2014 Midokura SARL
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# @author Jaume Devesa

import os

from neutron.db import db_base_plugin_v2 as base_db
from neutron.openstack.common import importutils
from neutron.openstack.common import uuidutils
from neutron.tests.unit import test_db_plugin
from oslo.config import cfg
from webob import exc

_uuid = uuidutils.generate_uuid

MIDOKURA_EXT_PATH = "midonet.neutron.extensions"


class MidonetNetworkTestPlugin(base_db.NeutronDbPluginV2):

    supported_extension_aliases = ['midonet-network']


class MidonetNetworkExtTestCase(test_db_plugin.NeutronDbPluginV2TestCase):

    fmt = 'json'

    def setUp(self):
        extensions_path = importutils.import_module(
            MIDOKURA_EXT_PATH).__file__
        cfg.CONF.set_override('api_extensions_path',
                              os.path.dirname(extensions_path))
        plugin = (__name__ + '.MidonetNetworkTestPlugin')
        super(MidonetNetworkExtTestCase, self).setUp(
            plugin=plugin)

    def test_inbound_is_uuid(self):
        """Test if new attributes for network are exposed.

        Best way to test this without being intrusive is to perform calls
        over the networks resource that have to fail because new attributes'
        validators not because attribute is not exposed.
        """
        data = {'network': {'name': 'net1',
                            'admin_state_up': True,
                            'tenant_id': _uuid(),
                            'midonet:inbound_filter_id': 'foo'}}
        req = self.new_create_request('networks', data, fmt=self.fmt)
        res = req.get_response(self.api)

        self.assertEqual(exc.HTTPBadRequest.code, res.status_int)
        body = self.deserialize(self.fmt, res)
        self.assertIn('NeutronError', body)
        message = body['NeutronError']['message']
        self.assertIn("'foo' is not a valid UUID", message)
