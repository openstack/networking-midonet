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

import setuptools


setuptools.setup(
    author='MidoNet',
    author_email='midonet-dev@midonet.org',
    entry_points={
        'console_scripts': [
            'midonet-db-manage = midonet.neutron.db.migration.cli:main']},
    description='Openstack Neutron MidoNet plugin',
    license="Apache License, Version 2.0",
    long_description=open("README.rst").read(),
    name='neutron-plugin-midonet',
    packages=setuptools.find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    url='http://www.midonet.org',
    version='2014.2+1',
    zip_safe=False,
)
