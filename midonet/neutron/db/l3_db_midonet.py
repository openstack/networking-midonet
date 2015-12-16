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

from oslo_utils import excutils

from neutron.callbacks import events
from neutron.callbacks import exceptions
from neutron.callbacks import registry
from neutron.callbacks import resources
from neutron.db import l3_gwmode_db
from neutron.extensions import l3


class MidonetL3DBMixin(l3_gwmode_db.L3_NAT_db_mixin):
    # TODO(kengo): This is temporary workaround until upstream adds a check
    # for router deletion in l3_db

    def _check_router_not_in_use(self, context, router_id):
        try:
            kwargs = {'context': context, 'router_id': router_id}
            registry.notify(
                resources.ROUTER, events.BEFORE_DELETE, self, **kwargs)
        except exceptions.CallbackFailure as e:
            with excutils.save_and_reraise_exception():
                if len(e.errors) == 1:
                    raise e.errors[0].error
                raise l3.RouterInUse(router_id=router_id, reason=e)
