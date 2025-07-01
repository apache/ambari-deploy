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

"""
Hosts Information Parser Module

This module provides functionality to parse host configuration information,
supporting wildcard patterns for machine names and IP addresses.
"""

from python.config_management.parsers import Parser
from python.exceptions.invalid_configuration_exception import *


class HostsInfoParser(Parser):
    """
    Parser for host information configuration.
    
    This class extends the base Parser to handle host configuration parsing,
    supporting wildcard patterns similar to Ansible hosts configuration.
    It can parse patterns like node[1-3], node[1-3]xx, or [1-3]node.
    """
    
    def parse_hosts(self, data):
        """
        Parse host patterns and expand wildcards.
        
        Args:
            data: String containing host pattern (e.g., 'node[1-3]')
            
        Returns:
            list: Expanded list of host names
        """
        hosts = self._expand_range(data)
        return hosts

    def parse(self, hosts_configurations):
        """
        Parse host configurations with support for wildcard patterns.
        
        Handles configurations like:
        ["10.1.1.[1-3] node[1-3].example.com password4"]
        
        Which expands to:
        [("node1.example.com","10.1.1.1","password4"),
         ("node2.example.com","10.1.1.2","password4"),
         ("node3.example.com","10.1.1.3","password4")]
        
        Args:
            hosts_configurations: List of host configuration strings in format
                                ["IP HOSTNAME PASSWORD", ...]
                                
        Returns:
            list: List of tuples containing (hostname, ip, password)
            
        Raises:
            InvalidConfigurationException: If configuration format is invalid
        """
        parsed_configs = []

        for config in hosts_configurations:
            if len(config.split()) != 3:
                raise InvalidConfigurationException

            if "[" in config:
                hostname_part, ip_part, password = config.split()
                hosts = []
                ips = []
                if "[" in hostname_part and "[" in ip_part:
                    hosts = self.parse_hosts(hostname_part)
                    ips = self.parse_hosts(ip_part)
                else:
                    raise InvalidConfigurationException

                if len(hosts) != len(ips):
                    raise InvalidConfigurationException("Configuration is invalid")
                for index, ip in enumerate(ips):
                    parsed_configs.append((hosts[index], ip, password))
            else:
                parsed_configs.append(tuple(config.split()))

        return parsed_configs
