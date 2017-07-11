# Copyright (C) 2016 Midokura SARL.
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

from oslo_serialization import jsonutils

from neutronclient.common import extension
from neutronclient.neutron import v2_0 as loggingV20

from midonet.neutron._i18n import _


def add_common_paramaters_to_arguments(parser):
    parser.add_argument(
        '--enabled',
        metavar='<True | False>',
        choices=['True', 'False'],
        help=_('Enable/disable for the logging. Defaults to False.'))
    parser.add_argument(
        '--description',
        dest='description',
        help=_('Description of logging.'))


def _format_firewall_logs(logging_resource):
    try:
        return '\n'.join([jsonutils.dumps(fw_log) for fw_log
                          in logging_resource['firewall_logs']])
    except (TypeError, KeyError):
        return ''


class LoggingResource(extension.NeutronClientExtension):
    resource = 'logging_resource'
    resource_plural = 'logging_resources'
    path = 'logging/logging_resources'
    object_path = '/%s' % path
    resource_path = '/%s/%%s' % path
    versions = ['2.0']


class LoggingResourceCreate(extension.ClientExtensionCreate, LoggingResource):
    """Create Logging Resource information."""

    shell_command = 'logging-create'

    def add_known_arguments(self, parser):
        parser.add_argument(
            'name', metavar='NAME',
            help=_('User defined logging name.'))
        add_common_paramaters_to_arguments(parser)

        return parser

    def args2body(self, args):
        body = {}
        attributes = ['name', 'description', 'tenant_id', 'enabled']
        loggingV20.update_dict(args, body, attributes)

        return {'logging_resource': body}


class LoggingResourceList(extension.ClientExtensionList, LoggingResource):
    """List Logging Resources."""

    shell_command = 'logging-list'
    list_columns = ['id', 'name', 'enabled']
    pagination_support = True
    sorting_support = True

    _formatters = {'firewall_logs': _format_firewall_logs, }


class LoggingResourceShow(extension.ClientExtensionShow, LoggingResource):
    """Show information of a given Logging Resource."""

    shell_command = 'logging-show'


class LoggingResourceDelete(extension.ClientExtensionDelete, LoggingResource):
    """Delete a given Logging Resource."""

    shell_command = 'logging-delete'


class LoggingResourceUpdate(extension.ClientExtensionUpdate, LoggingResource):
    """Update a given Logging Resource."""

    shell_command = 'logging-update'

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--name', dest='name',
            help=_('User defined logging name.'))
        add_common_paramaters_to_arguments(parser)

    def args2body(self, args):
        body = {}
        attributes = ['name', 'description', 'enabled']
        loggingV20.update_dict(args, body, attributes)

        return {'logging_resource': body}
