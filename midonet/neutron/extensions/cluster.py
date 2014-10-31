# Copyright (C) 2014 Midokura SARL
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import abc

from neutron.api import extensions
from neutron.api.v2 import base
from neutron import manager
from neutron.api.v2 import attributes as attr
from neutron.api.v2 import resource_helper

import six

CLUSTER = 'cluster'
CLUSTERS = '%ss' % CLUSTER

RESOURCE_ATTRIBUTE_MAP = {
    CLUSTERS: {
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'validate': {'type:string': None},
                      'is_visible': True, 'default': None},
    }
}


class Cluster(extensions.ExtensionDescriptor):
    """Cluster extension."""

    @classmethod
    def get_name(cls):
        return "Midonet Cluster Extension"

    @classmethod
    def get_alias(cls):
        return "cluster"

    @classmethod
    def get_description(cls):
        return "Cluster abstraction for basic cluster-related features"

    @classmethod
    def get_namespace(cls):
        return "http://docs.openstack.org/ext/cluster/api/v1.0"

    @classmethod
    def get_updated(cls):
        return "2014-11-01T10:00:00-00:00"

    @classmethod
    def get_resources(cls):
        exts = []
        plugin = manager.NeutronManager.get_plugin()
        collection_name = CLUSTERS
        params = RESOURCE_ATTRIBUTE_MAP.get(collection_name, dict())
        controller = base.create_resource(
            collection_name, CLUSTER, plugin, params)
        ex = extensions.ResourceExtension(collection_name, controller)
        exts.append(ex)
        return exts


@six.add_metaclass(abc.ABCMeta)
class ClusterPluginBase(object):

    @abc.abstractmethod
    def create_cluster(self, context, cluster):
        pass
