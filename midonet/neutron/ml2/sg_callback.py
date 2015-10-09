# Copyright (C) 2015 Midokura SARL.
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

from neutron.callbacks import events
from neutron.callbacks import registry
from neutron.callbacks import resources
from neutron import i18n

from oslo_log import helpers as log_helpers
from oslo_log import log as logging
from oslo_utils import excutils

_LE = i18n._LE
LOG = logging.getLogger(__name__)


class MidonetSecurityGroupsHandler(object):

    def __init__(self, client):
        self.client = client
        self.subscribe()

    @log_helpers.log_method_call
    def create_security_group(self, resource, event, trigger, **kwargs):
        sg = kwargs.get('security_group')
        try:
            self.client.create_security_group_postcommit(sg)
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Failed to create a security group %(sg_id)s "
                              "in Midonet: %(err)s"),
                          {"sg_id": sg["id"], "err": ex})
                try:
                    self.client.delete_security_group_postcommit(sg["id"])
                except Exception:
                    LOG.exception(_LE("Failed to delete security group %s"),
                                  sg['id'])

    @log_helpers.log_method_call
    def update_security_group(self, resource, event, trigger, **kwargs):
        pass

    @log_helpers.log_method_call
    def delete_security_group(self, resource, event, trigger, **kwargs):
        sg_id = kwargs.get('security_group_id')
        try:
            self.client.delete_security_group_postcommit(sg_id)
        except Exception as ex:
            LOG.error(_LE("Failed to a delete security group %(sg_id)s "
                          "in Midonet: %(err)s"),
                      {"sg_id": sg_id, "err": ex})

    @log_helpers.log_method_call
    def create_security_group_rule(self, resource, event, trigger, **kwargs):
        sgr = kwargs.get('security_group_rule')
        try:
            self.client.create_security_group_rule_postcommit(sgr)
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Failed to create a security group rule "
                              "%(sgr_id)s in Midonet: %(err)s"),
                          {"sgr_id": sgr["id"], "err": ex})
                try:
                    self.client.delete_security_group_rule_postcommit(
                        sgr["id"])
                except Exception:
                    LOG.exception(_LE("Failed to delete security group "
                                      " rule %s"),
                                  sgr['id'])

    @log_helpers.log_method_call
    def delete_security_group_rule(self, resource, event, trigger, **kwargs):
        sgr_id = kwargs.get('security_group_rule_id')
        try:
            self.client.delete_security_group_rule_postcommit(sgr_id)
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Failed to delete a security group %(sgr_id)s "
                              "in Midonet: %(err)s"),
                          {"sgr_id": sgr_id, "err": ex})

    def subscribe(self):
        # REVISIT(Ryu): Keep an extra set of strong references to the callback
        # methods so that they are not prematurely garbage collected.
        # This hack is required in the Liberty branch (not stable/kilo) because
        # currently the Liberty mechanism driver is expected to work with Kilo
        # ML2 plugin for MidoNet, and in Kilo ML2, there is a bug in which
        # these methods were referenced as weakrefs where a garbage collection
        # could remove these callbacks if they were part of an object.

        self._create_sg_f = self.create_security_group
        self._update_sg_f = self.update_security_group
        self._delete_sg_f = self.delete_security_group
        self._create_sgr_f = self.create_security_group_rule
        self._delete_sgr_f = self.delete_security_group_rule

        registry.subscribe(
            self._create_sg_f, resources.SECURITY_GROUP, events.AFTER_CREATE)
        registry.subscribe(
            self._update_sg_f, resources.SECURITY_GROUP, events.AFTER_UPDATE)
        registry.subscribe(
            self._delete_sg_f, resources.SECURITY_GROUP, events.AFTER_DELETE)
        registry.subscribe(
            self._create_sgr_f, resources.SECURITY_GROUP_RULE,
            events.AFTER_CREATE)
        registry.subscribe(
            self._delete_sgr_f, resources.SECURITY_GROUP_RULE,
            events.AFTER_DELETE)
