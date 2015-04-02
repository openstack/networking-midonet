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

from neutron.api.v2 import attributes
from neutron.common import constants
from neutron.common import exceptions as n_exc
from neutron.db import model_base
from neutron.db import portbindings_db
from neutron.extensions import portbindings
import sqlalchemy as sa
from sqlalchemy import orm


class PortBindingInfo(model_base.BASEV2):
    __tablename__ = 'midonet_port_bindings'

    port_id = sa.Column(sa.String(36),
                        sa.ForeignKey('portbindingports.port_id',
                                      ondelete="CASCADE"),
                        primary_key=True)
    interface_name = sa.Column(sa.String(length=255), nullable=False)
    binding = orm.relationship(portbindings_db.PortBindingPort,
                               backref=orm.backref("port_binding_info",
                                                   lazy='joined',
                                                   uselist=False,
                                                   cascade='delete'))


NIC_NAME_LEN = 14


def _get_tap_name(port_id):
    """ get the nova tap name. This is a dirty hack. If we have the tap name
    when nova creates the port, we can store it in the database immediately.
    nova does not provide us with a tap name, but there is only one way that
    it creates it, and it looks like the below.
    """
    devname = "tap" + port_id
    devname = devname[:NIC_NAME_LEN]
    return devname


class MidonetPortBindingMixin(object):

    def _is_driver_bound(self, dev_owner):
        return (dev_owner == constants.DEVICE_OWNER_DHCP or
                dev_owner.startswith('compute:'))

    def _get_interface_name(self, port):
        if self._is_driver_bound(port['device_owner']):
            return _get_tap_name(port['id'])
        else:
            binding_profile = port.get(portbindings.PROFILE)
            if not attributes.is_attr_set(binding_profile):
                return None
            return binding_profile.get('interface_name')

    def _get_host_name(self, port):
        return port.get(portbindings.HOST_ID)

    def _set_interface_name(self, session, port_id, interface_name):
        with session.begin(subtransactions=True):
            bind_port = session.query(
                PortBindingInfo).filter_by(port_id=port_id).first()
            if bind_port:
                if interface_name is None:
                    session.delete(bind_port)
                else:
                    bind_port.interface_name = interface_name
            else:
                session.add(PortBindingInfo(port_id=port_id,
                                            interface_name=interface_name))

    def _get_db_port_info(self, session, port_id):
        port_info = session.query(
            PortBindingInfo).filter_by(port_id=port_id).first()
        port_host = session.query(
            portbindings_db.PortBindingPort).filter_by(port_id=port_id).first()

        both_none = port_info is None and port_host is None
        both_set = port_info is not None and port_host is not None
        assert both_none or both_set
        if both_none:
            return None, None
        else:
            return port_host.host, port_info.interface_name

    def _get_port_info(self, port_data):
        if portbindings.PROFILE not in port_data:
            prof = attributes.ATTR_NOT_SPECIFIED
        else:
            prof = port_data.get(portbindings.PROFILE)
        if attributes.is_attr_set(prof) and 'interface_name' in prof:
            interface_name = prof['interface_name']
            if interface_name == '':
                interface_name = None
        else:
            interface_name = attributes.ATTR_NOT_SPECIFIED

        if portbindings.HOST_ID not in port_data:
            host = attributes.ATTR_NOT_SPECIFIED
        else:
            host = port_data.get(portbindings.HOST_ID)
            if host == '':
                host = None
        return host, interface_name

    def _validate_host_interface(self, host, if_name):

        def is_set(field):
            return attributes.is_attr_set(field)
        if not is_set(host) and is_set(if_name):
            msg = 'The host name must be set if the interface name is set'
            raise n_exc.BadRequest(resource='port', msg=msg)
        if is_set(host) and not is_set(if_name):
            msg = 'The interface name must be set if the host name is set'
            raise n_exc.BadRequest(resource='port', msg=msg)

    def _create_midonet_port_binding(self, context, port_id, port_data,
                                     new_port):
        host, name = self._get_port_info(port_data)
        if self._is_driver_bound(new_port['device_owner']):
            name = _get_tap_name(new_port['id'])
        else:
            self._validate_host_interface(host, name)
        if attributes.is_attr_set(name) and attributes.is_attr_set(host):
            if not self._is_driver_bound(new_port['device_owner']):
                prof = port_data.get(portbindings.PROFILE)
                new_port[portbindings.PROFILE] = prof
            self._set_interface_name(context.session, port_id, name)

    def _update_midonet_port_binding(self, context, port_id, old_port,
                                     port_data, port):
        old_host, old_name = self._get_port_info(old_port)
        new_host, new_name = self._get_port_info(port_data)
        if new_name == attributes.ATTR_NOT_SPECIFIED:
            new_name = old_name
        if new_host == attributes.ATTR_NOT_SPECIFIED:
            new_host = old_host

        if new_host is None and new_name is not None:
            msg = 'The host name must be set if the interface name is set'
            raise n_exc.BadRequest(resource='port', msg=msg)
        if new_name is None and new_host is not None:
            msg = 'The interface name must be set if the host name is set'
            raise n_exc.BadRequest(resource='port', msg=msg)
        if attributes.is_attr_set(new_name):
            if not self._is_driver_bound(port['device_owner']):
                prof = port_data.get(portbindings.PROFILE)
                port[portbindings.PROFILE] = prof
            self._set_interface_name(context.session, port_id, new_name)