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
Topology Manager Module

This module provides functionality for automatically generating cluster deployment topologies.
It can intelligently distribute services across nodes based on the cluster size and
component requirements. Future enhancements may include AI-driven topology generation
based on user environment and requirements.
"""

from enum import Enum

from python.config_management.service_map import *


class TopologyManager:
    """
    Manager class for generating cluster deployment topologies.
    
    This class automatically generates service distribution across nodes based on:
    - Number of available nodes
    - Required components
    - Service dependencies and co-location requirements
    
    Attributes:
        host_fetcher: Callable that returns list of available hosts
        host_groups: Dict mapping group names to lists of hosts
        group_services: Dict mapping group names to lists of services
        topology: Dict containing complete topology configuration
        components: List of components to be deployed
    """
    
    def __init__(self, host_fetcher, components):
        """
        Initialize the topology manager.
        
        Args:
            host_fetcher: Callable that returns list of available hosts
            components: List of components to be deployed
        """
        self.host_fetcher = host_fetcher
        self.host_groups = {}
        self.group_services = {}
        self.topology = {}
        self.components = components

    class Policy(Enum):
        """
        Enumeration of topology generation policies.
        
        THREE_NODE: Policy for 3-node clusters
        MULTI_NODE: Policy for clusters with 4+ nodes
        """
        THREE_NODE = 1
        MULTI_NODE = 2

    def determine_policy(self, hosts):
        """
        Determine the appropriate topology policy based on cluster size.
        
        Args:
            hosts (list): List of available hosts
            
        Returns:
            Policy: Selected topology policy (THREE_NODE or MULTI_NODE)
        """
        if len(hosts) == 3:
            return self.Policy.THREE_NODE
        else:
            return self.Policy.MULTI_NODE

    def generate_topology(self):
        """
        Generate complete cluster topology configuration.
        
        This method:
        1. Fetches available hosts
        2. Configures host groups
        3. Assigns services to groups
        4. Filters topology based on required components
        
        Returns:
            dict: Complete topology configuration with host_groups and group_services
        """
        hosts = self.host_fetcher()

        self._configure_hosts(hosts)
        self.topology = {
            "host_groups": self.host_groups,
            "group_services": self.group_services,
        }
        self.topology_filter()
        return self.topology

    def topology_filter(self):
        """
        Filter topology to include only required components.
        
        This method:
        1. Collects all service components for requested components
        2. Filters group services to include only required components
        """
        if len(self.components) == 0:
            return
        all_service_components = []
        for component_name in self.components:
            service_info = ServiceMap.get_service_info_by_component_name(component_name)
            service_components = service_info.get("server")
            all_service_components.extend(service_components)

        for group, services in self.topology["group_services"].items():
            self.topology["group_services"][group] = [
                service for service in services if service in all_service_components
            ]

    def _configure_hosts(self, hosts):
        """
        Configure host groups based on number of available hosts.
        
        For 3-node clusters: Creates 3 equal groups
        For 4+ node clusters: Creates 4 primary groups plus an additional group
        for remaining nodes if needed
        
        Args:
            hosts (list): List of available hosts
        """
        num_hosts = len(hosts)
        print(f"Group assignments: --- hosts: {hosts}")

        if num_hosts == 3:
            group_assignments = [(f"group{i}", [i]) for i in range(num_hosts)]
        elif num_hosts >= 4:
            group_assignments = [
                ("group0", [0]),
                ("group1", [1]),
                ("group2", [2]),
                ("group3", [3]),
            ]
            if num_hosts > 4:  # Assign fifth and subsequent hosts to group4
                group_assignments.append(("group4", list(range(4, num_hosts))))

        print(f"Group assignments: {group_assignments} hosts: {hosts}")
        self._assign_hosts_to_groups(group_assignments, hosts)

    def _assign_hosts_to_groups(self, group_assignments, hosts):
        """
        Assign hosts to groups and configure services for each group.
        
        Args:
            group_assignments (list): List of tuples (group_name, host_indices)
            hosts (list): List of available hosts
        """
        policy = self.determine_policy(hosts)
        for group_name, host_indices in group_assignments:
            self.host_groups[group_name] = [hosts[i] for i in host_indices]
            self.group_services[group_name] = self._get_services(
                int(group_name[-1]), policy
            )

    def _get_services(self, group_number, policy):
        """
        Get list of services for a specific group based on policy.
        
        The group number (0-4) corresponds to Ansible host group indices.
        Service distribution is optimized for high availability and
        performance based on standard deployment patterns.
        
        Args:
            group_number (int): Group index (0-4)
            policy (Policy): Topology policy to use
            
        Returns:
            list: List of services to be deployed in the group
        """
        services_a = {
            0: [
                "AMBARI_SERVER",
                "NAMENODE",
                "ZKFC",
                "JOURNALNODE",
                "RESOURCEMANAGER",
                "ZOOKEEPER_SERVER",
                "HBASE_MASTER",
                "HIVE_METASTORE",
                "SPARK_THRIFTSERVER",
                "FLINK_HISTORYSERVER",
                "HISTORYSERVER",
                "RANGER_TAGSYNC",
                "RANGER_USERSYNC",
                "KNOX_GATEWAY",
            ],
            1: [
                "NAMENODE",
                "ZKFC",
                "JOURNALNODE",
                "RESOURCEMANAGER",
                "ZOOKEEPER_SERVER",
                "HBASE_MASTER",
                "DATANODE",
                "NODEMANAGER",
                "APP_TIMELINE_SERVER",
                "RANGER_ADMIN",
                "METRICS_GRAFANA",
                "SPARK_JOBHISTORYSERVER",
                "KAFKA_BROKER",
                "ALLUXIO_MASTER",
                "INFRA_SOLR"
            ],
            2: [
                "ZOOKEEPER_SERVER",
                "JOURNALNODE",
                "DATANODE",
                "NODEMANAGER",
                "TIMELINE_READER",
                "YARN_REGISTRY_DNS",
                "METRICS_COLLECTOR",
                "HBASE_REGIONSERVER",
                "HIVE_SERVER",
                "WEBHCAT_SERVER",
                "INFRA_SOLR",
                "ALLUXIO_WORKER",
                "RANGER_KMS_SERVER",
            ],
        }

        services_b = {
            0: [
                "AMBARI_SERVER",
                "NAMENODE",
                "ZKFC",
                "JOURNALNODE",
                "RESOURCEMANAGER",
                "ZOOKEEPER_SERVER",
                "HBASE_MASTER",
                "FLINK_HISTORYSERVER",
                "ALLUXIO_MASTER",
            ],
            1: [
                "NAMENODE",
                "JOURNALNODE",
                "RESOURCEMANAGER",
                "ZKFC",
                "HBASE_MASTER",
                "ZOOKEEPER_SERVER",
                "HIVE_SERVER",
                "ALLUXIO_MASTER",
            ],
            2: [
                "APP_TIMELINE_SERVER",
                "RANGER_ADMIN",
                "METRICS_GRAFANA",
                "ZOOKEEPER_SERVER",
                "DATANODE",
                "NODEMANAGER",
                "SPARK_JOBHISTORYSERVER",
                "INFRA_SOLR",
                "JOURNALNODE",
                "KAFKA_BROKER",
                "HIVE_METASTORE",
                "SPARK_THRIFTSERVER",
                "HISTORYSERVER",
                "RANGER_USERSYNC",
                "ALLUXIO_MASTER",
            ],
            3: [
                "TIMELINE_READER",
                "YARN_REGISTRY_DNS",
                "METRICS_COLLECTOR",
                "HBASE_REGIONSERVER",
                "DATANODE",
                "NODEMANAGER",
                "WEBHCAT_SERVER",
                "KAFKA_BROKER",
                "RANGER_TAGSYNC",
                "ALLUXIO_WORKER",
                "KNOX_GATEWAY",
                "RANGER_KMS_SERVER",
                "INFRA_SOLR",
            ],
            4: [
                "NODEMANAGER",
                "DATANODE",
            ],
        }

        services = services_a if policy == self.Policy.THREE_NODE else services_b

        return services.get(group_number, [])


if __name__ == "__main__":
    topology = TopologyManager(
        lambda: ["server1", "server2", "server3", "server4", "server5"],
        [
            "hbase",
            "hdfs",
            "yarn",
            "hive",
            "zookeeper",
            "kafka",
            "spark",
            "flink",
            "ranger",
            "infra_solr",
            "ambari",
            "ambari_metrics",
            "kerberos",
        ],
    )
    print(topology.generate_topology())
    topology.topology_filter()
