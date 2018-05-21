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

from neutron_lib.db import utils as db_utils
from neutron_lib.exceptions import firewall_v1 as fw_exc
from oslo_db import exception as db_exc
from oslo_log import helpers as log_helpers
from oslo_utils import uuidutils
from sqlalchemy.orm import exc

from neutron.db import common_db_mixin

from midonet.neutron.db import logging_resource_model as model
from midonet.neutron.extensions import logging_resource as log_res_ext


class LoggingResourceDbMixin(log_res_ext.LoggingResourcePluginBase,
                             common_db_mixin.CommonDbMixin):
    """Mixin class to add logging resource."""

    __native_bulk_support = False

    @log_helpers.log_method_call
    def create_logging_resource(self, context, logging_resource):
        """Create a logging_resource"""
        log_res = logging_resource['logging_resource']
        with context.session.begin(subtransactions=True):
            log_res_db = model.LoggingResource(
                id=uuidutils.generate_uuid(),
                name=log_res['name'],
                description=log_res['description'],
                tenant_id=log_res['tenant_id'],
                enabled=log_res['enabled'])
            context.session.add(log_res_db)

        return self._make_logging_resource_dict(log_res_db)

    @log_helpers.log_method_call
    def get_logging_resource(self, context, id, fields=None):
        log_res_db = self._get_logging_resource(context, id)
        return self._make_logging_resource_dict(log_res_db, fields)

    @log_helpers.log_method_call
    def get_logging_resources(self, context, filters=None, fields=None,
                              sorts=None, limit=None, marker=None,
                              page_reverse=False):
        marker_obj = db_utils.get_marker_obj(self, context, 'logging_resource',
                                             limit, marker)

        return self._get_collection(
            context,
            model.LoggingResource,
            self._make_logging_resource_dict,
            filters=filters, fields=fields,
            sorts=sorts,
            limit=limit, marker_obj=marker_obj,
            page_reverse=page_reverse)

    @log_helpers.log_method_call
    def update_logging_resource(self, context, id, logging_resource):
        log_res = logging_resource['logging_resource']
        with context.session.begin(subtransactions=True):
            log_res_db = self._get_logging_resource(context, id)
            log_res_db.update(log_res)

        return self._make_logging_resource_dict(log_res_db)

    @log_helpers.log_method_call
    def delete_logging_resource(self, context, id):
        log_res_db = self._get_logging_resource(context, id)
        with context.session.begin(subtransactions=True):
            context.session.delete(log_res_db)

    @log_helpers.log_method_call
    def delete_logging_resource_firewall_log(self, context, id,
                                             logging_resource_id):
        f_log_db = self._get_firewall_log(context, id)
        with context.session.begin(subtransactions=True):
            context.session.delete(f_log_db)

    @log_helpers.log_method_call
    def create_logging_resource_firewall_log(
            self, context, firewall_log, logging_resource_id):
        f_log = firewall_log['firewall_log']
        try:
            with context.session.begin(subtransactions=True):
                f_log_db = model.FirewallLog(
                    id=uuidutils.generate_uuid(),
                    logging_resource_id=logging_resource_id,
                    tenant_id=f_log['tenant_id'],
                    description=f_log['description'],
                    fw_event=f_log['fw_event'],
                    firewall_id=f_log['firewall_id'])
                context.session.add(f_log_db)
        except db_exc.DBReferenceError:
            raise fw_exc.FirewallNotFound(firewall_id=f_log['firewall_id'])

        return self._make_firewall_log_dict(f_log_db)

    @log_helpers.log_method_call
    def get_logging_resource_firewall_log(self, context, id,
                                          logging_resource_id, fields=None):
        f_log_db = self._get_firewall_log(context, id)
        return self._make_firewall_log_dict(f_log_db, fields)

    @log_helpers.log_method_call
    def get_logging_resource_firewall_logs(self, context, logging_resource_id,
                                           filters=None, fields=None,
                                           sorts=None, limit=None,
                                           marker=None, page_reverse=False):
        marker_obj = db_utils.get_marker_obj(self, context, 'firewall_log',
                                             limit, marker)
        return self._get_collection(context,
                                    model.FirewallLog,
                                    self._make_firewall_log_dict,
                                    filters=filters, fields=fields,
                                    sorts=sorts,
                                    limit=limit, marker_obj=marker_obj,
                                    page_reverse=page_reverse)

    @log_helpers.log_method_call
    def get_firewall_logs(self, context, filters=None, fields=None,
                          sorts=None, limit=None, marker=None,
                          page_reverse=False):
        # This method is only for quota driver.
        return self._get_fw_logs_from_tenant(context, context.tenant_id)

    @log_helpers.log_method_call
    def update_logging_resource_firewall_log(
            self, context, id, logging_resource_id, firewall_log):
        f_log = firewall_log['firewall_log']
        with context.session.begin(subtransactions=True):
            f_log_db = self._get_firewall_log(context, id)
            f_log_db.update(f_log)

        return self._make_firewall_log_dict(f_log_db)

    def _get_logging_resource(self, context, id):
        try:
            query = self._model_query(context, model.LoggingResource)
            log_res_db = query.filter(model.LoggingResource.id == id).one()

        except exc.NoResultFound:
            raise log_res_ext.LoggingResourceNotFound(id=id)

        return log_res_db

    def _get_fw_logs_from_tenant(self, context, tenant_id):
        query = self._model_query(context, model.FirewallLog)
        return query.filter(model.FirewallLog.tenant_id == tenant_id).all()

    def _logging_resource_has_logs(self, context, log_res_id):
        query = self._model_query(context, model.FirewallLog)
        return bool(query.filter(
            model.FirewallLog.logging_resource_id == log_res_id).all())

    def _get_firewall_log(self, context, id):
        try:
            query = self._model_query(context, model.FirewallLog)
            f_log_db = query.filter(model.FirewallLog.id == id).one()

        except exc.NoResultFound:
            raise log_res_ext.FirewallLogNotFound(id=id)

        return f_log_db

    def _make_logging_resource_dict(self, log_res_db, fields=None):
        res = {'id': log_res_db['id'],
               'name': log_res_db['name'],
               'description': log_res_db['description'],
               'tenant_id': log_res_db['tenant_id'],
               'enabled': log_res_db['enabled']}

        # extend parameter for specific resource types
        res.update(self._extend_resource_specific_loggings(log_res_db))

        return self._fields(res, fields)

    def _extend_resource_specific_loggings(self, log_res_db, fields=None):
        # Currently, only firewall log is returned.
        return {
            'firewall_logs': [
                self._make_firewall_log_dict(f_log, fields)
                for f_log in log_res_db.firewall_logs
                if log_res_db.firewall_logs
            ]
        }

    def _make_firewall_log_dict(self, f_log_db, fields=None):
        res = {'id': f_log_db['id'],
               'tenant_id': f_log_db['tenant_id'],
               'description': f_log_db['description'],
               'logging_resource_id': f_log_db['logging_resource_id'],
               'fw_event': f_log_db['fw_event'],
               'firewall_id': f_log_db['firewall_id']}
        return self._fields(res, fields)
