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

from neutron_lib.api import extensions


class Fip64(extensions.ExtensionDescriptor):
    """Floating IPv6 for IPv4 instances (NAT64)."""

    @classmethod
    def get_name(cls):
        return "MidoNet FIP64 Extension"

    @classmethod
    def get_alias(cls):
        return "fip64"

    @classmethod
    def get_description(cls):
        return "MidoNet FIP64 Extension"

    @classmethod
    def get_updated(cls):
        return "2016-12-14T10:00:00-00:00"
