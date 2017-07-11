# Copyright 2015 Midokura SARL
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

from neutron_lib.api.definitions import port as port_def
from neutron_lib.api.definitions import portbindings
from neutron_lib.api import validators
from neutron_lib.db import model_base
from neutron_lib import exceptions as n_exc
from neutron_lib.plugins import directory
import sqlalchemy as sa
from sqlalchemy import orm

from neutron.db import _resource_extend as resource_extend
from neutron.db import models_v2


class PortBindingInfo(model_base.BASEV2):
    __tablename__ = 'midonet_port_bindings'

    port_id = sa.Column(sa.String(36),
                        sa.ForeignKey('ports.id'),
                        sa.ForeignKey('portbindingports.port_id',
                                      ondelete="CASCADE"),
                        primary_key=True)
    interface_name = sa.Column(sa.String(length=255), nullable=False)
    port = orm.relationship(models_v2.Port,
                            backref=orm.backref("port_binding_info",
                                                lazy='joined',
                                                uselist=False,
                                                cascade='delete'))


@resource_extend.has_resource_extenders
class MidonetPortBindingMixin(object):

    def _extend_mido_portbinding(self, port_res, if_name):
        if if_name:
            port_res[portbindings.PROFILE] = {"interface_name": if_name}
        else:
            port_res[portbindings.PROFILE] = {}

    def _process_mido_portbindings_create_and_update(self, context, port_data,
                                                     port):

        port_id = port['id']

        # Set profile to {} if the binding:profile key exists but set to None.
        # This is for the special handling in the case the user wants to remove
        # the binding.
        profile = None
        if portbindings.PROFILE in port_data:
            profile = port_data.get(portbindings.PROFILE) or {}
        profile_set = validators.is_attr_set(profile)

        if_name = profile.get('interface_name') if profile_set else None
        if profile_set and profile:
            # Update or create, so validate the inputs
            if not if_name:
                msg = 'The interface name was not provided or empty'
                raise n_exc.BadRequest(resource='port', msg=msg)

            if self.get_port_host(context, port_id) is None:
                msg = 'Cannot set binding because the host is not bound'
                raise n_exc.BadRequest(resource='port', msg=msg)

        with context.session.begin(subtransactions=True):
            bind_port = context.session.query(PortBindingInfo).filter_by(
                port_id=port_id).first()
            if profile_set:
                if bind_port:
                    if if_name:
                        bind_port.interface_name = if_name
                    else:
                        context.session.delete(bind_port)
                elif if_name:
                    context.session.add(PortBindingInfo(
                        port_id=port_id, interface_name=if_name))
            else:
                if_name = bind_port.interface_name if bind_port else None

        self._extend_mido_portbinding(port, if_name)

    @staticmethod
    @resource_extend.extends([port_def.COLLECTION_NAME])
    def _extend_port_mido_portbinding(port_res, port_db):
        bind_port = port_db.port_binding_info
        if_name = bind_port.interface_name if bind_port else None
        plugin = directory.get_plugin()
        plugin._extend_mido_portbinding(port_res, if_name)
