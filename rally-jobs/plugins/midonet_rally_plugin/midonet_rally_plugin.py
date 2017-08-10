#
# Copyright 2016 Midokura SARL
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Rally Plugin to manage MidoNet resources"""

from __future__ import print_function

import netaddr
import random
import string
import utils

from rally.common import logging
from rally.task import atomic
from rally.task import scenario

AUTH_TOKEN = utils.RequestScenario._get_token()
LOG = logging.getLogger(__name__)


class MidonetRallyPluginMixin(object):

    def _execute_api(self, method, api, header, data=None):
        """Execute REST API call

        :param method: http method
        :param api: api for resource
        :param header: http header
        :param data: data fields for the resource
        :returns: HTTP status

        Depending on method provided, it executes appropriate REST call.
        If token expires, it regenerates auth token.
        """
        if method == "GET_ALL":
            val = self.request_get_all(api, header)
            if val != 401:
                return val
        elif method == "POST":
            val = self.request_post(api, header, data)
        elif method == "PUT":
            val = self.request_put(api, header, data)
        elif method == "GET_RESOURCE":
            val = self.request_get_resource(api, header)
        else:
            val = self.request_delete(api, header)
        if val == 401:
            global AUTH_TOKEN
            LOG.debug("Authentication token expired..!!")
            LOG.debug("Retrieving new Auth token and continuing operations")
            AUTH_TOKEN = utils.RequestScenario._get_token()
            header["X-Auth-Token"] = AUTH_TOKEN
            val = self._execute_api(method, api, header, data)
            LOG.debug("Executed value: ", val)
            return val

    @atomic.action_timer("create_bridge")
    def _create_bridge(self, method, api, header, data):
        """Benchmark create MidoNet bridge with REST API

        :param method: http method
        :param api: api for bridge
        :param header: http header
        :param data: data fields for the resource
        """
        self._execute_api(method, api, header, data)

    @atomic.action_timer("delete_bridge")
    def _delete_bridge(self, method, api, header, data):
        """Benchmark delete MidoNet bridge through REST API

        :param method: http method
        :param api: api for MidoNet bridge
        :param header: http header
        :param data: data fields for the resource
        """
        self._execute_api(method, api, header)

    @atomic.action_timer("create_router")
    def _create_router(self, method, api, header, data):
        """Benchmark create MidoNet router with REST API

        :param method: http method
        :param api: api for router
        :param header: http header
        :param data: data fields for the resource
        """
        self._execute_api(method, api, header, data)

    @atomic.action_timer("delete_router")
    def _delete_router(self, method, api, header, data):
        """Benchmark delete MidoNet router with REST API

        :param method: http method
        :param api: api for router
        :param header: http header
        :param data: data fields for the resource
        """
        self._execute_api(method, api, header, data)

    def _get_or_create_midonet_router(self, media_type):
        """Get the details of MidoNet routers

        It gets the list of all available MidoNet routers and parse its output
        to get the value of router id. In case if no router is available then
        new router is created.

        :param media_type: media type required for MidoNet router
        :returns : router id
        """
        router_api = "routers"
        col_media_type = media_type[:28] + 'collection.' + media_type[28:]
        header_get = {"Accept": col_media_type, "X-Auth-Token": "%s"
                      % AUTH_TOKEN}
        router_details = self._execute_api("GET_ALL", router_api, header_get)
        if not len(router_details) == 0:
            router_id = router_details[0]["id"]
        else:
            header_post = {"Content-Type": media_type, "X-Auth-Token": "%s"
                           % AUTH_TOKEN}
            # create a random name for router
            router_name = ''.join(random.choice(string.ascii_lowercase)
                                  for x in range(6))
            data = {"name": router_name, "tenantId": ""}
            # create router
            self._execute_api("POST", router_api, header_post, data)

            # get the router id
            router_details = self._execute_api("GET_ALL", router_api,
                                               header_get)
            router_id = router_details[0]["id"]

        return router_id

    @atomic.action_timer("create_router_port")
    def _create_router_port(self, method, api, header, data):
        """Benchmark create MidoNet port with REST API

        :param method: http method
        :param api: api for port
        :param header: http header
        :param data: data fields for the resource
        """
        self._execute_api(method, api, header, data)

    @atomic.action_timer("delete_router_port")
    def _delete_router_port(self, method, api, header, data):
        """Benchmark delete MidoNet port with REST API

        :param method: http method
        :param api: api for port
        :param header: http header
        :param data: data fields for the resource
        """
        self._execute_api(method, api, header, data)


@scenario.configure(name="MidonetRallyPlugin.create_midonet_bridge")
class CreateMidonetBridge(MidonetRallyPluginMixin, utils.RequestScenario):

    def run(self, api, media_type, no_of_bridges):
        """Create MidoNet bridge with REST API

        :param api: api for MidoNet bridge
        :param media_type: media type required for MidoNet bridge
        :param no_of_bridges: number of bridges to be created in one iteration
        """
        # header for bridge API
        header = {"Content-Type": media_type, "X-Auth-Token": "%s" %
                                                              AUTH_TOKEN}
        for _ in range(no_of_bridges):
            # generate payload for creating bridge
            # creating bridge requires bridge name
            # bridge name is generated randomly
            bridge_name = ''.join(random.choice(string.ascii_lowercase) for x
                                  in range(10))
            data = {"name": bridge_name, "tenantId": ""}
            # create bridge
            self._create_bridge("POST", api, header, data)


@scenario.configure(name="MidonetRallyPlugin.delete_midonet_bridge")
class DeleteMidonetBridge(MidonetRallyPluginMixin, utils.RequestScenario):

    def run(self, api, media_type):
        """Deletes all available bridges

        :param api: api for MidoNet bridge
        :param media_type: media type required for MidoNet bridge
        """
        # to delete all the bridges, retrieve IDs of bridge
        # header for router GET command
        header = {"X-Auth-Token": "%s" % AUTH_TOKEN}
        bridge_details = self._execute_api("GET_ALL", api, header)

        # parse the result of bridge GET command
        # to get only IDs of bridge
        bridge_ids = [bridge["id"] for bridge in bridge_details]
        LOG.debug("Number of bridges to be deleted are: %s" % len(bridge_ids))

        # update header for delete API
        header["Content-Type"] = media_type
        # delete midonet routers
        [self._delete_bridge("DELETE", api + "/" + bridge_id, header)
         for bridge_id in bridge_ids]


@scenario.configure(name="MidonetRallyPlugin.create_midonet_router")
class CreateMidonetRouter(MidonetRallyPluginMixin, utils.RequestScenario):

    def run(self, api, media_type, no_of_routers):
        """Create MidoNet router with REST API

        :param api: api for creating MidoNet router
        :param media_type: media type for creating MidoNet router
        :param no_of_routers: number of routers to be created in one iteration
        """

        # header for router API
        header = {"Content-Type": media_type, "X-Auth-Token": "%s" %
                                                              AUTH_TOKEN}
        for _ in range(no_of_routers):
            # generate payload for creating router
            # creating router requires router name
            # router name is generated randomly
            router_name = ''.join(random.choice(string.ascii_lowercase)
                                  for x in range(10))
            data = {"name": router_name, "tenantId": ""}
            # create router
            self._create_router("POST", api, header, data)


@scenario.configure(name="MidonetRallyPlugin.delete_midonet_router")
class DeleteMidonetRouter(MidonetRallyPluginMixin, utils.RequestScenario):

    def run(self, api, media_type):
        """Deletes all available routers

        :param api: api for MidoNet router
        :param media_type: media type required for MidoNet router
        """

        # to delete all the routers, retrieve IDs of router
        col_media_type = media_type[:28] + 'collection.' + media_type[28:]

        # header for router GET command
        header_get = {"Accept": col_media_type, "X-Auth-Token": "%s"
                      % AUTH_TOKEN}
        router_details = self._execute_api("GET_ALL", api, header_get)
        # parse the result of router GET command
        # to get only IDs of router
        router_ids = [router["id"] for router in router_details]
        LOG.debug("Number of routers to be deleted are: %s" % len(router_ids))

        # update header for delete API
        header_del = {"Content-Type": media_type, "X-Auth-Token": "%s" %
                      AUTH_TOKEN}
        # delete midonet routers
        [self._delete_router("DELETE", api + "/" + router_id, header_del)
         for router_id in router_ids]


@scenario.configure(name="MidonetRallyPlugin.create_midonet_router_port")
class CreateMidonetRouterPort(MidonetRallyPluginMixin, utils.RequestScenario):

    def run(self, api, media_type, data, no_of_ports):
        """Create port on MidoNet router

        :param api: api for MidoNet port
        :param media_type: media type required for MidoNet port
        :param data: payload data for MidoNet router port
        :param no_of_ports: number of ports to be created at one time
        """
        # router id is retrieved with router get command
        # the first router id available is used for the operation
        router_id = self._get_or_create_midonet_router(media_type['router'])
        post_api = "routers/" + router_id + "/" + api
        # set header with content-type and authentication token
        header = {"Content-Type": media_type['port'], "X-Auth-Token": "%s"
                  % AUTH_TOKEN}
        cidr = data["networkAddress"] + '/' + data["networkLength"]
        ip_list = netaddr.IPNetwork(cidr)

        for _ in range(no_of_ports):
            # port address is generated randomly in the cidr
            port_address = str(random.choice(ip_list))
            LOG.debug("port_address is: %s" % port_address)
            data["portAddress"] = port_address
            # create port
            self._create_router_port("POST", post_api, header, data)


@scenario.configure(name="MidonetRallyPlugin.delete_midonet_port")
class DeleteMidonetPort(MidonetRallyPluginMixin, utils.RequestScenario):

    def run(self, api, media_type):
        """Deletes all available ports

        :param api: api for MidoNet port
        :param media_type: media type required for MidoNet port
        """

        col_media_type = media_type['port'][:28] + 'collection.' \
            + media_type['port'][28:]
        # header for get command
        header_get = {"Accept": col_media_type, "X-Auth-Token": "%s"
                                                                % AUTH_TOKEN}
        port_details = self._execute_api("GET_ALL", api, header_get)

        # get the all available ports
        ports = [port["id"] for port in port_details]
        LOG.debug("Number of ports to be deleted are: %s" % len(ports))

        # update header for delete API
        header_del = {"Content-Type": media_type['port'], "X-Auth-Token": "%s"
                      % AUTH_TOKEN}
        # delete midonet ports
        [self._delete_router_port("DELETE", api + "/" + port_id, header_del)
         for port_id in ports]
