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

"""Logging Resource action implementations"""

import logging

from osc_lib.command import command
from osc_lib import exceptions
from osc_lib import utils

from neutronclient.neutron import v2_0 as neutronV20

from midonet.neutron._i18n import _, _LE
# REVISIT(yamamoto): should not import openstackclient?
from openstackclient.identity import common as identity_common


LOG = logging.getLogger(__name__)


_formatters = {
}


def _get_columns(item):
    columns = list(item.keys())
    if 'tenant_id' in columns:
        columns.remove('tenant_id')
        if 'project_id' not in columns:
            columns.append('project_id')
    return tuple(sorted(columns))


def _get_attrs(client_manager, parsed_args):
    attrs = {}
    if parsed_args.description is not None:
        attrs['description'] = parsed_args.description
    if parsed_args.enable:
        attrs['enabled'] = True
    if parsed_args.disable:
        attrs['enabled'] = False
    # It is possible that name is not updated during 'set'
    if parsed_args.name is not None:
        attrs['name'] = str(parsed_args.name)
    # The remaining options do not support 'set' command, so they require
    # additional check
    if 'project' in parsed_args and parsed_args.project is not None:
        # TODO(singhj): since 'project' logic is common among
        # router, network, port etc., maybe move it to a common file.
        identity_client = client_manager.identity
        project_id = identity_common.find_project(
            identity_client,
            parsed_args.project,
            parsed_args.project_domain,
        ).id
        attrs['tenant_id'] = project_id
    return attrs


def _add_updatable_args(parser):
    admin_group = parser.add_mutually_exclusive_group()
    admin_group.add_argument(
        '--enable',
        action='store_true',
        help=_("Enable logging resource")
    )
    admin_group.add_argument(
        '--disable',
        action='store_true',
        help=_("Disable logging resource (Default)")
    )
    parser.add_argument(
        '--description',
        metavar='<description>',
        help=_("Description of this logging resource")
    )


def _get_id(client, name_or_id):
    return neutronV20.find_resourceid_by_name_or_id(
        client, 'logging_resource', name_or_id)


class CreateLoggingResource(command.ShowOne):
    _description = _("Create a new logging resource")

    def get_parser(self, prog_name):
        parser = super(CreateLoggingResource, self).get_parser(prog_name)
        _add_updatable_args(parser)
        parser.add_argument(
            '--project',
            metavar='<project>',
            help=_("Owner's project (name or ID)")
        )
        identity_common.add_project_domain_option_to_parser(parser)
        parser.add_argument(
            'name',
            metavar='<name>',
            help=_("Name of this logging resource")
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.neutronclient
        attrs = _get_attrs(self.app.client_manager, parsed_args)
        obj = client.create_logging_resource(
            {'logging_resource': attrs})['logging_resource']
        columns = _get_columns(obj)
        data = utils.get_dict_properties(obj, columns, formatters=_formatters)
        return (columns, data)


class DeleteLoggingResource(command.Command):
    _description = _("Delete logging resource(s)")

    def get_parser(self, prog_name):
        parser = super(DeleteLoggingResource, self).get_parser(prog_name)
        parser.add_argument(
            'logging_resource',
            metavar="<logging resource>",
            nargs="+",
            help=_("Logging Resource(s) to delete (name or ID)")
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.neutronclient
        result = 0
        for resource in parsed_args.logging_resource:
            try:
                id_ = _get_id(client, resource)
                client.delete_logging_resource(id_)
            except Exception as e:
                result += 1
                LOG.error(_LE("Failed to delete logging resource with "
                              "name or ID '%(resource)s': %(e)s"),
                          {'resource': resource, 'e': e})
        if result > 0:
            total = len(parsed_args.logging_resource)
            msg = (_("%(result)s of %(total)s logging resources failed "
                   "to delete.") % {'result': result, 'total': total})
            raise exceptions.CommandError(msg)


class ListLoggingResource(command.Lister):
    _description = _("List logging resources")

    def get_parser(self, prog_name):
        parser = super(ListLoggingResource, self).get_parser(prog_name)
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.neutronclient
        columns = (
            'id',
            'name',
        )
        column_headers = (
            'ID',
            'Name',
        )
        data = client.list_logging_resources()['logging_resources']
        return (column_headers,
                (utils.get_dict_properties(
                    s, columns,
                    formatters=_formatters,
                ) for s in data))


class SetLoggingResource(command.Command):
    _description = _("Set logging resource properties")

    def get_parser(self, prog_name):
        parser = super(SetLoggingResource, self).get_parser(prog_name)
        parser.add_argument(
            'logging_resource',
            metavar="<logging resource>",
            help=_("Logging Resource to display (name or ID)")
        )
        parser.add_argument(
            '--name',
            metavar="<name>",
            help=_("Set logging resource name")
        )
        _add_updatable_args(parser)
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.neutronclient
        attrs = _get_attrs(self.app.client_manager, parsed_args)
        id_ = _get_id(client, parsed_args.logging_resource)
        client.update_logging_resource(id_, {'logging_resource': attrs})


class ShowLoggingResource(command.ShowOne):
    _description = _("Display logging resource details")

    def get_parser(self, prog_name):
        parser = super(ShowLoggingResource, self).get_parser(prog_name)
        parser.add_argument(
            'logging_resource',
            metavar="<logging resource>",
            help=_("Logging Resource to display (name or ID)")
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.neutronclient
        id_ = _get_id(client, parsed_args.logging_resource)
        obj = client.show_logging_resource(id_)['logging_resource']
        columns = _get_columns(obj)
        data = utils.get_dict_properties(obj, columns, formatters=_formatters)
        return (columns, data)
