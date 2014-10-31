# Copyright 2014 OpenStack Foundation
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

import mock
from webob import exc

from neutron.openstack.common import uuidutils
from neutron.tests.unit import test_api_v2
from neutron.tests.unit import test_api_v2_extension

from midonet.neutron.extensions import cluster

_uuid = uuidutils.generate_uuid
_get_path = test_api_v2._get_path


class ClusterExtensionTestCase(test_api_v2_extension.ExtensionTestCase):
    fmt = "json"

    def setUp(self):
        super(ClusterExtensionTestCase, self).setUp()
        plural_mappings = {'cluster': 'clusters'}
        self._setUpExtension(
            'midonet.neutron.extensions.cluster.ClusterPluginBase',
            None, cluster.RESOURCE_ATTRIBUTE_MAP,
            cluster.Cluster, '', plural_mappings=plural_mappings)

    def test_rebuild(self):
        data = {'cluster': {'tenant_id': _uuid()}}
        instance = self.plugin.return_value
        instance.create_cluster.return_value = {}

        res = self.api.post(_get_path('clusters', fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt)
        self.assertEqual(exc.HTTPCreated.code, res.status_int)
        instance.create_cluster.assert_called_once_with(mock.ANY, cluster=data)


class ClusterExtensionTestCaseXml(ClusterExtensionTestCase):
    fmt = "xml"
