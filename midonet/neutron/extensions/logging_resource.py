# Copyright (C) 2016 Midokura SARL
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

import six

from oslo_config import cfg

from neutron_lib.api.definitions import logging_resource
from neutron_lib.api import extensions as api_extensions
from neutron_lib import exceptions as nexception
from neutron_lib.plugins import directory

from neutron.api import extensions
from neutron.api.v2 import base
from neutron.api.v2 import resource_helper
from neutron.quota import resource_registry

from midonet.neutron._i18n import _
from midonet.neutron.common import constants


class LoggingResourceNotFound(nexception.NotFound):
    message = _("Logging resource %(id)s does not exist")


class FirewallLogNotFound(nexception.NotFound):
    message = _("Firewall log %(id)s does not exist")


class ResourceInUseByLoggingResource(nexception.InUse):
    message = _("%(resource_name)s %(resource_id)s %(reason)s")

    def __init__(self, **kwargs):
        if 'reason' not in kwargs:
            kwargs['reason'] = "is in use by logging resource"
        super(ResourceInUseByLoggingResource, self).__init__(**kwargs)


FW_EVENT_ACCEPT = logging_resource.FW_EVENT_ACCEPT
FW_EVENT_DROP = logging_resource.FW_EVENT_DROP
FW_EVENT_ALL = logging_resource.FW_EVENT_ALL
FW_EVENTS = logging_resource.FW_EVENTS

# A tenant may want to create firewall logs for all firewalls in tenant.
# Set default quotas to align with default quota_firewall of 10.

firewall_log_quota_opts = [
    cfg.IntOpt('quota_firewall_log',
               default=10,
               help=_('Number of firewall logs allowed per tenant. '
                      'A negative value means unlimited.'))
]
cfg.CONF.register_opts(firewall_log_quota_opts, 'QUOTAS')


class Logging_resource(api_extensions.APIExtensionDescriptor):
    """Logging resource extension."""

    api_definition = logging_resource

    @classmethod
    def get_resources(cls):
        """Returns Ext Resources."""

        plural_mappings = resource_helper.build_plural_mappings(
            {}, logging_resource.RESOURCE_ATTRIBUTE_MAP)

        resources = resource_helper.build_resource_info(
            plural_mappings,
            logging_resource.RESOURCE_ATTRIBUTE_MAP,
            constants.LOGGING_RESOURCE)
        plugin = directory.get_plugin(constants.LOGGING_RESOURCE)

        for collection_name in logging_resource.SUB_RESOURCE_ATTRIBUTE_MAP:
            resource_name = collection_name[:-1]
            resource_registry.register_resource_by_name(resource_name)
            parent = logging_resource.SUB_RESOURCE_ATTRIBUTE_MAP[
                collection_name].get('parent')
            params = logging_resource.SUB_RESOURCE_ATTRIBUTE_MAP[
                collection_name].get('parameters')

            controller = base.create_resource(collection_name, resource_name,
                                              plugin, params,
                                              allow_bulk=True,
                                              parent=parent)

            resource = extensions.ResourceExtension(
                collection_name,
                controller, parent,
                path_prefix=logging_resource.API_PREFIX,
                attr_map=params)
            resources.append(resource)

        return resources


@six.add_metaclass(abc.ABCMeta)
class LoggingResourcePluginBase(object):

    path_prefix = logging_resource.API_PREFIX

    @abc.abstractmethod
    def create_logging_resource(self, context, logging_resource):
        pass

    @abc.abstractmethod
    def update_logging_resource(self, context, id, logging_resource):
        pass

    @abc.abstractmethod
    def delete_logging_resource(self, context, id):
        pass

    @abc.abstractmethod
    def get_logging_resources(self, context, filters=None, fields=None,
                              sorts=None, limit=None, marker=None,
                              page_reverse=False):
        pass

    @abc.abstractmethod
    def get_logging_resource(self, context, id, fields=None):
        pass

    @abc.abstractmethod
    def create_logging_resource_firewall_log(self, context,
                                             logging_resource_id,
                                             firewall_log):
        pass

    @abc.abstractmethod
    def update_logging_resource_firewall_log(
            self, context, id, logging_resource_id, firewall_log):
        pass

    @abc.abstractmethod
    def delete_logging_resource_firewall_log(self, context,
                                             id, logging_resource_id):
        pass

    @abc.abstractmethod
    def get_logging_resource_firewall_logs(self, context, logging_resource_id,
                                           filters=None, fields=None,
                                           sorts=None, limit=None,
                                           marker=None, page_reverse=False):
        pass

    @abc.abstractmethod
    def get_logging_resource_firewall_log(self, context, id,
                                          logging_resource_id, fields=None):
        pass
