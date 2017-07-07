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


from neutron_lib.callbacks import events
from neutron_lib.callbacks import registry
from neutron_lib.callbacks import resources

from oslo_log import helpers as log_helpers
from oslo_log import log as logging
from oslo_utils import excutils

LOG = logging.getLogger(__name__)


@registry.has_registry_receivers
class MidonetSecurityGroupsHandler(object):

    def __init__(self, client):
        self.client = client

    # TODO(yamamoto): Implement PRECOMMIT hooks for task-based api
    # (bug 1694699)
    @registry.receives(resources.SECURITY_GROUP, [events.AFTER_CREATE])
    @log_helpers.log_method_call
    def create_security_group(self, resource, event, trigger, **kwargs):
        sg = kwargs.get('security_group')
        try:
            self.client.create_security_group_postcommit(sg)
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to create a security group %(sg_id)s "
                          "in Midonet: %(err)s",
                          {"sg_id": sg["id"], "err": ex})
                try:
                    self.client.delete_security_group_postcommit(sg["id"])
                except Exception:
                    LOG.exception("Failed to delete security group %s",
                                  sg['id'])

    @registry.receives(resources.SECURITY_GROUP, [events.AFTER_UPDATE])
    @log_helpers.log_method_call
    def update_security_group(self, resource, event, trigger, **kwargs):
        pass

    @registry.receives(resources.SECURITY_GROUP, [events.AFTER_DELETE])
    @log_helpers.log_method_call
    def delete_security_group(self, resource, event, trigger, **kwargs):
        sg_id = kwargs.get('security_group_id')
        try:
            self.client.delete_security_group_postcommit(sg_id)
        except Exception as ex:
            LOG.error("Failed to a delete security group %(sg_id)s "
                      "in Midonet: %(err)s",
                      {"sg_id": sg_id, "err": ex})

    @registry.receives(resources.SECURITY_GROUP_RULE, [events.AFTER_CREATE])
    @log_helpers.log_method_call
    def create_security_group_rule(self, resource, event, trigger, **kwargs):
        sgr = kwargs.get('security_group_rule')
        try:
            self.client.create_security_group_rule_postcommit(sgr)
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to create a security group rule "
                          "%(sgr_id)s in Midonet: %(err)s",
                          {"sgr_id": sgr["id"], "err": ex})
                try:
                    self.client.delete_security_group_rule_postcommit(
                        sgr["id"])
                except Exception:
                    LOG.exception("Failed to delete security group  rule %s",
                                  sgr['id'])

    @registry.receives(resources.SECURITY_GROUP_RULE, [events.AFTER_DELETE])
    @log_helpers.log_method_call
    def delete_security_group_rule(self, resource, event, trigger, **kwargs):
        sgr_id = kwargs.get('security_group_rule_id')
        try:
            self.client.delete_security_group_rule_postcommit(sgr_id)
        except Exception as ex:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to delete a security group %(sgr_id)s "
                          "in Midonet: %(err)s",
                          {"sgr_id": sgr_id, "err": ex})
