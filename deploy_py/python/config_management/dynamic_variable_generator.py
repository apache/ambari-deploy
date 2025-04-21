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
Dynamic Variable Generator Module

This module is responsible for generating dynamic variables used in:
- Cluster configuration templates
- Ansible deployment automation
- Service configuration

The generator creates variables based on:
- Host group configurations
- Service distributions
- Network settings
- Repository configurations
"""

import os
import socket

from python.common.constants import *
from python.config_management.template_renderer import *
from python.utils.os_utils import *


class DynamicVariableGenerator:
    """
    Generates dynamic variables for cluster configuration and deployment.
    
    This class handles:
    - Host group variable generation
    - Service distribution mapping
    - Repository URL configuration
    - Network and database settings
    
    Attributes:
        advanced_conf: Advanced configuration object
        group_services: Mapping of groups to their services
        hosts_groups: Mapping of groups to their hosts
        template_renderer: Template rendering utility
    """

    def __init__(self, advanced_conf):
        """
        Initialize the dynamic variable generator.

        Args:
            advanced_conf: Advanced configuration object containing
                         deployment settings and service distributions
        """
        self.advanced_conf = advanced_conf
        self.group_services = self.advanced_conf.get("group_services")
        self.hosts_groups = self.advanced_conf.get("host_groups")
        self.template_renderer = TemplateRenderer()

    def generate(self):
        """
        Generate all dynamic variables.

        Returns:
            dict: Complete set of generated variables
        """
        conf = self.generate_dynamic_j2template_variables()
        return conf

    def get_kdc_server_host(self):
        """
        Get the KDC server hostname.
        
        Returns:
            str: KDC server hostname (external or Ambari server host)
        """
        if (
            len(self.advanced_conf.get("security_options")["external_hostname"].strip())
            > 0
        ):
            return self.advanced_conf.get("security_options")["external_hostname"]
        else:
            ambari_server_host = self.get_ambari_server_host()
            return ambari_server_host

    def get_ambari_server_host(self):
        """
        Get the Ambari server hostname.
        
        Returns:
            str: Ambari server hostname
            
        Raises:
            InvalidConfigurationException: If Ambari server is not configured
        """
        ambari_server_group = None
        for group_name, services in self.group_services.items():
            if "AMBARI_SERVER" in services:
                ambari_server_group = group_name
                break
        if ambari_server_group:
            ambari_server_host = self.hosts_groups[ambari_server_group][0]
            return ambari_server_host
        else:
            raise InvalidConfigurationException

    def generate_hosts_groups_variables(self):
        """
        Generate host group variables for all services.
        
        Maps services to their host groups and creates lists of hosts
        for each service type (e.g., namenode_hosts, zookeeper_hosts).
        
        Returns:
            dict: Mapping of service types to their host lists
        """
        group_hosts = {}
        hosts_groups_variables = {}

        for group_name, hosts in self.hosts_groups.items():
            group_hosts[group_name] = hosts

        for group_name, group_services in self.group_services.items():
            if "NAMENODE" in group_services:
                hosts_groups_variables.setdefault("namenode_hosts", []).extend(
                    group_hosts[group_name]
                )
            if "ZKFC" in group_services:
                hosts_groups_variables.setdefault("zkfc_hosts", []).extend(
                    group_hosts[group_name]
                )
            if "RESOURCEMANAGER" in group_services:
                hosts_groups_variables.setdefault("resourcemanager_hosts", []).extend(
                    group_hosts[group_name]
                )
            if "JOURNALNODE" in group_services:
                hosts_groups_variables.setdefault("journalnode_hosts", []).extend(
                    group_hosts[group_name]
                )
            if "ZOOKEEPER_SERVER" in group_services:
                hosts_groups_variables.setdefault("zookeeper_hosts", []).extend(
                    group_hosts[group_name]
                )
            if "HIVE_SERVER" in group_services or "HIVE_METASTORE" in group_services:
                hosts_groups_variables.setdefault("hiveserver_hosts", []).extend(
                    group_hosts[group_name]
                )
            if "KAFKA_BROKER" in group_services:
                hosts_groups_variables.setdefault("kafka_hosts", []).extend(
                    group_hosts[group_name]
                )
            if "RANGER_ADMIN" in group_services:
                hosts_groups_variables.setdefault("rangeradmin_hosts", []).extend(
                    group_hosts[group_name]
                )
            if "RANGER_KMS_SERVER" in group_services:
                hosts_groups_variables.setdefault("rangerkms_hosts", []).extend(
                    group_hosts[group_name]
                )
            if "SOLR_SERVER" in group_services:
                hosts_groups_variables.setdefault("solr_hosts", []).extend(
                    group_hosts[group_name]
                )

        # Remove duplicates from host lists
        for k, v in hosts_groups_variables.items():
            hosts_groups_variables[k] = list(set(v))
        return hosts_groups_variables

    def generate_dynamic_j2template_variables(self):
        """
        Generate dynamic variables for Jinja2 templates.
        
        This method:
        1. Generates base variables from advanced configuration
        2. Adds dynamic variables for blueprints and deployment
        3. Configures repository settings
        4. Merges all variables into final configuration
        
        Returns:
            dict: Complete set of template variables
        """
        str_conf = self.advanced_conf.get_str_conf()
        
        # Generate extra variables needed for blueprints and deployment
        ambari_repo_url = self._generate_ambari_repo_url()
        extra_vars = {
            "ntp_server_hostname": self._generate_ntp_server_hostname(),
            "hadoop_base_dir": self.advanced_conf.get("data_dirs")[0],
            "kdc_hostname": self.get_kdc_server_host(),
            "database_hostname": self._generate_database_host(),
            "ambari_server_host": self.get_ambari_server_host(),
            "ambari_repo_url": ambari_repo_url,
        }
        
        # Merge configurations
        conf_j2_context = self.advanced_conf.get_conf()
        conf_j2_context.update(extra_vars)
        hosts_groups_variables = self.generate_hosts_groups_variables()
        
        # Render template with merged configuration
        rendered_conf_vars = self.template_renderer.render_template(
            str_conf, conf_j2_context
        ).decode_result(decoder="yaml")
        rendered_conf_vars.update(hosts_groups_variables)
        rendered_conf_vars.update(extra_vars)
        
        # Configure repositories
        if not rendered_conf_vars["repos"]:
            rendered_conf_vars["repos"] = []
        if not self.advanced_conf.is_ambari_repo_configured():
            rendered_conf_vars["repos"].append(
                {"name": "ambari_repo", "url": ambari_repo_url}
            )
        return rendered_conf_vars

    def _generate_ntp_server_hostname(self):
        """
        Generate NTP server hostname.
        
        Returns:
            str: NTP server hostname (external or Ambari server host)
        """
        if len(self.advanced_conf.get("external_ntp_server_hostname").strip()) > 0:
            return self.advanced_conf.get("external_ntp_server_hostname").strip()
        else:
            ambari_server_host = self.get_ambari_server_host()
            return ambari_server_host

    def _generate_database_host(self):
        """
        Generate database host configuration.
        
        Returns:
            str: Database hostname (external or Ambari server host)
        """
        ambari_host = self.get_ambari_server_host()
        external_database_server_ip = self.advanced_conf.get("database_options")[
            "external_hostname"
        ]
        if len(external_database_server_ip.strip()) == 0:
            database_host = ambari_host
        else:
            database_host = self.advanced_conf.get("database_options")[
                "external_hostname"
            ]
        return database_host

    def get_ip_address(self):
        """
        Get the local IP address.
        
        Returns:
            str: Local IP address or error message
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(("8.8.8.8", 80))
            ip_address = sock.getsockname()[0]
            return ip_address
        except socket.error:
            return "Unable to retrieve IP address"

    def _generate_ambari_repo_url(self):
        """
        Generate Ambari repository URL based on configuration.
        The URL generation follows these rules:
        1. If user has configured repos in base_conf.yml, use that URL directly
        2. If using local packages (repo_pkgs_dir):
           - For create_http_repo_for_local_pkgs=true: Generate HTTP URL pointing to the HTTP server
           - For create_http_repo_for_local_pkgs=false: Generate file:// URL pointing to local path
        
        Note: The repository structure is determined by setup_repo.sh:
        - For YUM repos: Directly serves from repository root
        - For APT repos: Creates and serves from 'dists/jammy/main/binary-amd64'
                        URL format: 'deb [trusted=yes] http://host:port/ jammy main'
        
        Returns:
            str: Generated repository URL
        """
        ambari_repo_url = ""
        # For docker deployment, this will be the IP of the container running the deployment script
        # Otherwise, it will be the IP of the host machine running the deployment script
        if self.advanced_conf.get("local_repo_ipaddress", "") is not "":
            ipaddress = self.advanced_conf.get("local_repo_ipaddress")
        else:
            ipaddress = self.get_ip_address()
        http_port = self.advanced_conf.get("http_repo_port", 8881)
        create_http_repo = self.advanced_conf.get("create_http_repo_for_local_pkgs", False)
        repo_pkgs_dir = self.advanced_conf.get("repo_pkgs_dir", "")

        if not self.advanced_conf.is_ambari_repo_configured():
            if self.advanced_conf.has_repo_pkgs():
                if create_http_repo:
                    # Generate HTTP URL for remote access
                    ambari_repo_url = f"http://{ipaddress}:{http_port}"
                else:
                    ambari_repo_url = f"file://{repo_pkgs_dir}"
                print(f"[DEBUG] Generated repository URL: {ambari_repo_url}")
        else:
            # Use user-configured repository URL
            repos = self.advanced_conf.get("repos", [])
            for repo_item in repos:
                if "ambari_repo" == repo_item["name"]:
                    ambari_repo_url = repo_item["url"]
                    print(f"[DEBUG] Using configured repository URL: {ambari_repo_url}")
                    break

        return ambari_repo_url
