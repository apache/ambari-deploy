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
Group Configuration Consistency Validator Module

This module is responsible for validating the consistency of host group configurations, including:
- Uniqueness of machine names within host groups
- Matching between host group configuration and hosts.yml
- Validity of service component deployment
- Consistency of host group names
"""

from python.config_management.configurations.advanced_configuration import *
from python.config_management.configurations.hosts_info_configuration import *

from .service_map import *
from .validator import *


class GroupConsistencyValidator(Validator):
    """
    Host Group Configuration Consistency Validator
    
    This class is responsible for validating:
    - Correctness of host group configurations
    - Validity of service component distribution
    - Existence of hostnames in hosts configuration
    - Consistency of host group names across different configurations
    
    Attributes:
        hosts_info_conf: Hosts information configuration object
        host_groups: Host group configuration information
        host_group_services: Host group services configuration information
    """

    def __init__(
        self,
        advanced_conf: AdvancedConfiguration,
        hosts_info_conf: HostsInfoConfiguration,
    ):
        """
        Initialize the host group consistency validator
        
        Args:
            advanced_conf: Advanced configuration object containing host groups and service distribution info
            hosts_info_conf: Hosts configuration object containing detailed information for all hosts
        """
        super().__init__()
        self.hosts_info_conf = hosts_info_conf.get_conf()
        self.host_groups = advanced_conf.get("host_groups")
        self.host_group_services = advanced_conf.get("group_services")

    def validate(self):
        """
        Perform host group configuration consistency validation
        
        Validates:
        1. Parse all hosts defined in hosts configuration
        2. Verify uniqueness of machine names within host groups
        3. Verify all machines in host groups are defined in hosts configuration
        4. Verify no duplicate service components within each group
        5. Verify all service components are supported
        6. Verify consistency of host group names across configurations
        
        Returns:
            self: Returns the validator itself for method chaining
        """
        parsed_hosts = self.hosts_info_conf.get("hosts")
        conf_defined_hosts = {}  # Store host information defined in hosts configuration
        host_groups_group_names = []  # Store group names from host_groups
        host_group_services_group_names = []  # Store group names from group_services

        # Parse hosts configuration and build host mapping
        for host_info_str in parsed_hosts:
            host_info = host_info_str.split()
            ip = host_info[0]
            hostname = host_info[1]
            passwd = host_info[2]
            conf_defined_hosts[hostname] = ip

        # Validate host group configuration
        for group_name, group_hosts in self.host_groups.items():
            host_groups_group_names.append(group_name)
            # Check for duplicate machine names within group
            if len(list(set(group_hosts))) != len(group_hosts):
                self.err_messages.append(
                    "Each machine name can only be listed once within the same group."
                )
            # Check if machines are defined in hosts configuration
            for host_name in group_hosts:
                if host_name not in conf_defined_hosts:
                    self.err_messages.append(
                        f"{host_name} defined in conf.yml but not configured in hosts.yml."
                    )

        # Validate service component configuration
        for group_name, services in self.host_group_services.items():
            host_group_services_group_names.append(group_name)
            # Check for duplicate service components within group
            duplicated_services = [
                sname for sname in services if services.count(sname) >= 2
            ]
            if len(duplicated_services) > 0:
                self.err_messages.append(
                    f"Each deployed component name can only be listed once within the same group. Please check the configuration of the following group: {group_name}, component name: {' '.join(list(set(duplicated_services)))}"
                )

            # Verify if service components are supported
            for service_name in services:
                is_supported = ServiceMap.is_service_supported(service_name)
                if not is_supported:
                    self.err_messages.append(
                        "{}The selected component for deployment is currently not supported.".format(
                            service_name
                        )
                    )

        # Verify consistency between host_groups and group_services group names
        if not (
            len(host_groups_group_names) == len(host_group_services_group_names)
            and set(host_groups_group_names) == set(host_group_services_group_names)
        ):
            self.err_messages.append(
                "The host_groups configuration and the group names in group_services are inconsistent."
            )

        return self
