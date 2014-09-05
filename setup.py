#!/usr/bin/env python

# Copyright (c) 2014 Midokura Europe SARL, All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from distutils import core
import setuptools


core.setup(
    author='Midokura',
    author_email='mido-openstack-dev@midokura.com',
    description='Neutron is a virtual network service for Openstack',
    license="Apache License, Version 2.0",
    long_description=open("README.rst").read(),
    name='neutron-plugin-midonet',
    packages=setuptools.find_packages(),
    url='https://github.com/midokura/python-neutron-plugin-midonet',
    version='2014.2-mido1',
    zip_safe=False,
)
