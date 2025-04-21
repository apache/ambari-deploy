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

from ipaddress import ip_address

from python.config_management.configurations.hosts_info_configuration import *

from .validator import *


class HostsInfoValidator(Validator):
    def __init__(self, hosts_info_conf: HostsInfoConfiguration):
        super().__init__()
        self.hosts_info_conf = hosts_info_conf.get_conf()

    def validate(self):
        parsed_hosts = self.hosts_info_conf.get("hosts")

        # Validate IP addresses
        for host in parsed_hosts:
            ip, hostname, _ = host.split()
            if not HostsInfoValidator._is_valid_ip(ip):
                self.err_messages.append(f"Invalid IP address: {ip}")

        # Additional validations can be added here (e.g., hostname format)

        return self

    @staticmethod
    def _is_valid_ip(ip):
        try:
            ip_address(ip)
            return True
        except ValueError:
            return False
