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
Service Map Module

This module defines the mapping between services and their components in the big data ecosystem.
It provides utility methods to:
- Validate service and component support
- Retrieve service information
- Map service components to their parent services
"""

from python.exceptions.invalid_configuration_exception import *


class ServiceMap:
    """
    A utility class that manages service and component mappings.
    
    This class provides static methods to:
    - Validate service and component support
    - Retrieve service configuration information
    - Map between services and their components
    
    The service map is the core configuration for automated deployment,
    defining which components belong to each service and maintaining
    consistency with Ambari's component definitions for blueprint compatibility.
    """
    
    @staticmethod
    def get_service_key_from_service(service_name):
        """
        Get the service key for a given service component name.
        
        Args:
            service_name (str): Name of the service component (e.g., 'NAMENODE')
            
        Returns:
            str: Service key (e.g., 'hdfs' for 'NAMENODE')
            
        Raises:
            InvalidConfigurationException: If service is not found in the map
        """
        for service_key, service_info in ServiceMap.get_services_map().items():
            if service_name in service_info["server"]:
                return service_key
        raise InvalidConfigurationException(
            f"Service '{service_name}' not found in services map."
        )

    @staticmethod
    def is_service_supported(service_name):
        """
        Check if a service component is supported.
        
        Args:
            service_name (str): Name of the service component to check
            
        Returns:
            bool: True if the service is supported, False otherwise
        """
        for service_key, info in ServiceMap.get_services_map().items():
            if service_name in info["server"]:
                return True
        return False

    @staticmethod
    def is_component_supported(component_name):
        """
        Check if a service component type is supported.
        
        Args:
            component_name (str): Name of the component type to check
                                (e.g., 'hdfs', 'hbase')
            
        Returns:
            bool: True if the component type is supported, False otherwise
        """
        comps = [
            service_key for service_key, info in ServiceMap.get_services_map().items()
        ]
        if component_name in comps:
            return True
        return False

    @staticmethod
    def get_service_info(service_name):
        """
        Get service configuration information for a service component.
        
        Args:
            service_name (str): Name of the service component
            
        Returns:
            dict: Service configuration information including server and client components,
                 or None if service is not supported
        """
        key = ServiceMap.get_service_key_from_service(service_name)
        if ServiceMap.is_service_supported(service_name):
            return ServiceMap.get_services_map().get(key)
        else:
            return None

    @staticmethod
    def get_service_info_by_component_name(component_name):
        """
        Get service configuration information by component type name.
        
        Args:
            component_name (str): Name of the component type (e.g., 'hdfs', 'hbase')
            
        Returns:
            dict: Service configuration information including server and client components
        """
        return ServiceMap.get_services_map().get(component_name)

    @staticmethod
    def get_services_map():
        """
        Get the complete service component mapping.
        
        This is the core configuration for automated deployment. It defines which components
        belong to each big data service. The component names in both 'server' and 'clients'
        must match Ambari's component definitions to ensure blueprint compatibility.
        
        Returns:
            dict: Complete mapping of services to their server and client components
        """
        service_map = {
            "hbase": {
                "server": ["HBASE_MASTER", "HBASE_REGIONSERVER"],
                "clients": ["HBASE_CLIENT"],
            },
            "hdfs": {
                "server": [
                    "NAMENODE",
                    "DATANODE",
                    "SECONDARY_NAMENODE",
                    "JOURNALNODE",
                    "ZKFC",
                ],
                "clients": ["HDFS_CLIENT", "MAPREDUCE2_CLIENT"],
            },
            "yarn": {
                "server": [
                    "NODEMANAGER",
                    "RESOURCEMANAGER",
                    "HISTORYSERVER",
                    "APP_TIMELINE_SERVER",
                    "YARN_REGISTRY_DNS",
                    "TIMELINE_READER",
                ],
                "clients": ["YARN_CLIENT"],
            },
            "hive": {
                "server": ["HIVE_METASTORE", "WEBHCAT_SERVER", "HIVE_SERVER"],
                "clients": ["HIVE_CLIENT", "HCAT", "TEZ_CLIENT"],
            },
            "zookeeper": {
                "server": ["ZOOKEEPER_SERVER"],
                "clients": ["ZOOKEEPER_CLIENT"],
            },
            "kafka": {
                "server": [
                    "KAFKA_BROKER",
                ],
                "clients": [],
            },
            "spark": {
                "server": ["SPARK_JOBHISTORYSERVER", "SPARK_THRIFTSERVER"],
                "clients": ["SPARK_CLIENT"],
            },
            "flink": {"server": ["FLINK_HISTORYSERVER"], "clients": ["FLINK_CLIENT"]},
            "ranger": {
                "server": ["RANGER_ADMIN", "RANGER_TAGSYNC", "RANGER_USERSYNC"],
                "clients": [],
            },
            "ranger_kms": {"server": ["RANGER_KMS_SERVER"], "clients": []},
            "infra_solr": {"server": ["INFRA_SOLR"], "clients": ["INFRA_SOLR_CLIENT"]},
            "solr": {"server": ["SOLR_SERVER"], "clients": []},
            "ambari": {"server": ["AMBARI_SERVER"], "clients": []},
            "ambari_metrics": {
                "server": ["METRICS_COLLECTOR", "METRICS_GRAFANA"],
                "clients": ["METRICS_MONITOR"],
            },
            "kerberos": {"server": ["KERBEROS_CLIENT"], "clients": ["KERBEROS_CLIENT"]},
            "knox": {"server": ["KNOX_GATEWAY"], "clients": []},
            "alluxio": {"server": ["ALLUXIO_MASTER", "ALLUXIO_WORKER"], "clients": []},
        }
        return service_map
