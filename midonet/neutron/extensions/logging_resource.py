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

from neutron_lib.api import converters
from neutron_lib.api import extensions as api_extensions
from neutron_lib.db import constants as db_const
from neutron_lib import exceptions as nexception
from neutron_lib.plugins import directory
from oslo_config import cfg
import six

from midonet.neutron._i18n import _
from midonet.neutron.common import constants
from neutron.api import extensions
from neutron.api.v2 import base
from neutron.api.v2 import resource_helper
from neutron.quota import resource_registry


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


LOGGING_PREFIX = '/logging'
FW_EVENT_ACCEPT = 'ACCEPT'
FW_EVENT_DROP = 'DROP'
FW_EVENT_ALL = 'ALL'
FW_EVENTS = [FW_EVENT_ACCEPT, FW_EVENT_DROP, FW_EVENT_ALL]
LOG_COMMON_FIELDS = {
    'id': {'allow_post': False, 'allow_put': False,
           'validate': {'type:uuid': None},
           'is_visible': True, 'primary_key': True},
    'tenant_id': {'allow_post': True, 'allow_put': False,
                  'required_by_policy': True, 'is_visible': True},
    'logging_resource_id': {'allow_post': False, 'allow_put': False,
                            'is_visible': True}
}

RESOURCE_ATTRIBUTE_MAP = {
    'logging_resources': {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None}, 'is_visible': True,
               'primary_key': True},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'required_by_policy': True, 'is_visible': True},
        'name': {'allow_post': True, 'allow_put': True,
                 'validate': {'type:string': db_const.NAME_FIELD_SIZE},
                 'default': '', 'is_visible': True},
        'description': {
            'allow_post': True, 'allow_put': True,
            'validate': {'type:string': db_const.LONG_DESCRIPTION_FIELD_SIZE},
            'default': '', 'is_visible': True},
        'enabled': {'allow_post': True, 'allow_put': True,
                    'is_visible': True, 'default': False,
                    'convert_to': converters.convert_to_boolean},
        'firewall_logs': {'allow_post': False, 'allow_put': False,
                          'is_visible': True}
    }
}

SUB_RESOURCE_ATTRIBUTE_MAP = {
    'firewall_logs': {
        'parent': {'collection_name': 'logging_resources',
                   'member_name': 'logging_resource'},
        'parameters': dict((LOG_COMMON_FIELDS),
                      **{
                        'description': {
                            'allow_post': True, 'allow_put': True,
                            'validate': {
                                'type:string':
                                    db_const.LONG_DESCRIPTION_FIELD_SIZE},
                            'default': '', 'is_visible': True},
                        'firewall_id': {
                            'allow_post': True, 'allow_put': False,
                            'is_visible': True,
                            'validate': {'type:uuid': None}},
                        'fw_event': {
                            'allow_post': True, 'allow_put': True,
                            'is_visible': True,
                            'validate': {'type:values': FW_EVENTS},
                            'default': FW_EVENT_ALL}
                      })
    },
}

# A tenant may want to create firewall logs for all firewalls in tenant.
# Set default quotas to align with default quota_firewall of 10.

firewall_log_quota_opts = [
    cfg.IntOpt('quota_firewall_log',
               default=10,
               help=_('Number of firewall logs allowed per tenant. '
                      'A negative value means unlimited.'))
]
cfg.CONF.register_opts(firewall_log_quota_opts, 'QUOTAS')


class Logging_resource(api_extensions.ExtensionDescriptor):
    """Logging resource extension."""

    @classmethod
    def get_name(cls):
        return "Midonet Logging Resource Extension"

    @classmethod
    def get_alias(cls):
        return "logging-resource"

    @classmethod
    def get_description(cls):
        return "The logging resource extension."

    @classmethod
    def get_namespace(cls):
        return "http://docs.openstack.org/ext/logging_resource/api/v2.0"

    @classmethod
    def get_updated(cls):
        return "2016-06-06T10:00:00-00:00"

    @classmethod
    def get_resources(cls):
        """Returns Ext Resources."""

        plural_mappings = resource_helper.build_plural_mappings(
            {}, RESOURCE_ATTRIBUTE_MAP)

        resources = resource_helper.build_resource_info(
            plural_mappings,
            RESOURCE_ATTRIBUTE_MAP,
            constants.LOGGING_RESOURCE)
        plugin = directory.get_plugin(constants.LOGGING_RESOURCE)

        for collection_name in SUB_RESOURCE_ATTRIBUTE_MAP:
            resource_name = collection_name[:-1]
            resource_registry.register_resource_by_name(resource_name)
            parent = SUB_RESOURCE_ATTRIBUTE_MAP[collection_name].get('parent')
            params = SUB_RESOURCE_ATTRIBUTE_MAP[collection_name].get(
                'parameters')

            controller = base.create_resource(collection_name, resource_name,
                                              plugin, params,
                                              allow_bulk=True,
                                              parent=parent)

            resource = extensions.ResourceExtension(
                collection_name,
                controller, parent,
                path_prefix=LOGGING_PREFIX,
                attr_map=params)
            resources.append(resource)

        return resources

    def get_extended_resources(self, version):
        if version == "2.0":
            return RESOURCE_ATTRIBUTE_MAP
        else:
            return {}


@six.add_metaclass(abc.ABCMeta)
class LoggingResourcePluginBase(object):

    path_prefix = LOGGING_PREFIX

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
