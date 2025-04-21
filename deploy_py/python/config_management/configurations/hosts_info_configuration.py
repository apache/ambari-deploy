"""
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from python.common.constants import *
from python.config_management.hosts_info_parser import HostsInfoParser

from .base_configuration import BaseConfiguration


class HostsInfoConfiguration(BaseConfiguration, HostsInfoParser):
    def __init__(self, name=HOSTS_CONF_NAME):
        super().__init__(name)

    def get_hosts_info(self):
        hosts_info_arr = self.get_conf()
        return hosts_info_arr.get("hosts")

    def get_user(self):
        hosts_info_arr = self.get_conf()
        return hosts_info_arr.get("user", "root")
