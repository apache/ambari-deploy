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
Service Manager Module

This module manages service installation and client configuration for the cluster.
It handles:
- Service discovery across host groups
- Client component identification
- Service dependency resolution
"""

from python.config_management.service_map import *


class ServiceManager:
    """
    Manages service installation and client configuration.
    
    This class is responsible for:
    - Identifying services to be installed
    - Determining required client components
    - Managing service dependencies
    
    Attributes:
        advanced_conf: Advanced configuration object containing service distributions
    """

    def __init__(self, advanced_conf):
        """
        Initialize the service manager.

        Args:
            advanced_conf: Advanced configuration object containing
                         service and host group configurations
        """
        self.advanced_conf = advanced_conf

    def get_services_need_install(self):
        """
        Get list of services that need to be installed.
        
        Collects all unique services across all host groups.
        
        Returns:
            list: Unique list of services to be installed
            
        Example:
            For host groups:
            {
                'group1': ['NAMENODE', 'DATANODE'],
                'group2': ['DATANODE', 'NODEMANAGER']
            }
            Returns: ['NAMENODE', 'DATANODE', 'NODEMANAGER']
        """
        group_services = self.advanced_conf.get("group_services")
        services = []
        for group_name, host_components in group_services.items():
            services.extend(host_components)
        return list(set(services))

    def get_service_clients_need_install(self, services):
        """
        Get list of client components needed for the services.
        
        For each service, identifies required client components
        based on service mapping information.
        
        Args:
            services (list): List of services to check for required clients
            
        Returns:
            list: Unique list of client components to be installed
            
        Example:
            For services ['HDFS', 'HIVE']:
            Returns: ['HDFS_CLIENT', 'HIVE_CLIENT']
        """
        clients = []
        for service_name in services:
            service_info = ServiceMap.get_service_info(service_name)
            if service_info and "clients" in service_info:
                clients.extend(service_info["clients"])
        return list(set(clients))
