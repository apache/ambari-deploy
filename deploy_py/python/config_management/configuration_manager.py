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

# -*- coding: UTF-8 -*-
"""
Configuration management module for cluster deployment.

This module handles all aspects of configuration management including:
- Loading and parsing configuration files
- Generating derived configurations
- Validating configurations
- Managing Ambari and Ansible configurations

The configuration flow:
1. Load base configuration
2. Generate derived configurations
3. Validate all configurations
4. Save configurations for deployment
"""

from python.common.basic_logger import get_logger
from python.common.constants import *
from python.config_management.conf_validator import *
from python.config_management.configurations.advanced_configuration import *
from python.config_management.configurations.ambari_blueprint_configuration import *
from python.config_management.configurations.ambari_cluster_template_configuration import *
from python.config_management.configurations.ansible_host_configuration import *
from python.config_management.configurations.ansible_var_configuration import *
from python.config_management.configurations.hosts_info_configuration import *
from python.config_management.configurations.standard_configuration import *
from python.config_management.group_consistency_validator import *
from python.config_management.hosts_info_validator import *
from python.config_management.topology_validator import *
from python.config_management.validation_manager import *
from python.utils.os_utils import *

logger = get_logger()


class ConfigurationManager:
    """
    Manages the complete lifecycle of deployment configurations.
    
    This class is responsible for:
    - Loading base configurations
    - Generating derived configurations
    - Validating configuration consistency
    - Saving deployment configurations
    
    Attributes:
        base_conf_name (str): Name of the base configuration file
        sd_conf (StandardConfiguration): Standard configuration handler
        validators (list): List of configuration validators
        allowed_methods (set): Set of allowed method names for dynamic access
    """

    def __init__(self, base_conf_name):
        """
        Initialize the configuration manager.

        Args:
            base_conf_name (str): Name of the base configuration file
        """
        self.base_conf_name = base_conf_name
        self.sd_conf = StandardConfiguration(self.base_conf_name)
        self.validators = []
        self.allowed_methods = {
            "is_ambari_repo_configured",
            "has_any_ambari_repo",
            "has_repo_pkgs"
        }

    def __getattr__(self, name):
        """
        Dynamic method access handler.

        Provides access to specific methods from advanced configuration.

        Args:
            name (str): Name of the requested attribute

        Returns:
            callable: Method from advanced configuration if available

        Raises:
            AttributeError: If the requested method is not allowed or doesn't exist
        """
        if name in self.allowed_methods:
            def method(*args, **kwargs):
                if self.advanced_conf and hasattr(self.advanced_conf, name):
                    return getattr(self.advanced_conf, name)(*args, **kwargs)
                else:
                    raise AttributeError(
                        f"'{type(self.advanced_conf).__name__}' object has no attribute '{name}'"
                    )
            return method
        else:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )

    def load_confs(self):
        """
        Load all required configurations.
        
        Initializes:
        - Hosts information configuration
        - Advanced configuration
        """
        self.hosts_info_conf = HostsInfoConfiguration()
        self.advanced_conf = AdvancedConfiguration()

    def generate_confs(self, save=False):
        """
        Generate all derived configurations.

        Args:
            save (bool): Whether to save the generated configurations to disk

        Raises:
            ValueError: If configuration validation fails
        """
        cv = ConfValidator(self.sd_conf)
        err = cv.validate().err_messages
        if err:
            error_messages = "\n".join(err)
            raise ValueError(
                f"Configuration validation failed with the following errors:\n{error_messages}"
            )

        self.hosts_info_conf = self.sd_conf.generate_conf(
            StandardConfiguration.GenerateConfType.HostsInfoConfiguration, save
        )
        self.advanced_conf = self.sd_conf.generate_conf(
            StandardConfiguration.GenerateConfType.AdvancedConfiguration, save
        )

    def save_ambari_configurations(self):
        """
        Save Ambari-specific configurations.
        
        Generates and saves:
        - Ambari cluster template
        - Ambari blueprint configuration
        """
        stack_version = self.sd_conf.get("stack_version", "3.2.0")
        ambari_cluster_template_conf = AmbariClusterTemplateConfiguration(
            "cluster_template.json", DynamicVariableGenerator(self.advanced_conf)
        )
        ambari_cluster_template_conf.save()

        ambari_blue_print_conf = AmbariBluePrintConfiguration(
            "blueprint.json",
            DynamicVariableGenerator(self.advanced_conf),
            ServiceManager(self.advanced_conf),
            stack_version,
        )
        ambari_blue_print_conf.save()

    def setup_validators(self):
        """
        Set up configuration validators.
        
        Initializes validators for:
        - Topology validation
        - Group consistency
        - Hosts information
        """
        self.validators.append(TopologyValidator(self.advanced_conf))
        self.validators.append(
            GroupConsistencyValidator(self.advanced_conf, self.hosts_info_conf)
        )
        self.validators.append(HostsInfoValidator(self.hosts_info_conf))

    def validate_configurations(self):
        """
        Validate all configurations using registered validators.

        Raises:
            ValueError: If any validation fails
        """
        validation_manager = ValidationManager(self.validators)
        errors = validation_manager.validate_all()
        if errors:
            error_messages = "\n".join(errors)
            raise ValueError(
                f"Configuration validation failed with the following errors:\n{error_messages}"
            )

    def save_ansible_configurations(self):
        """
        Save Ansible-specific configurations.
        
        Generates and saves:
        - Ansible variables configuration
        - Ansible hosts configuration
        """
        AnsibleVarConfiguration(
            "all", DynamicVariableGenerator(self.advanced_conf)
        ).save()
        AnsibleHostConfiguration(
            "hosts",
            self.hosts_info_conf,
            self.sd_conf,
            DynamicVariableGenerator(self.advanced_conf),
        ).save()


if __name__ == "__main__":
    # Example usage of ConfigurationManager
    config_manager = ConfigurationManager(BASE_CONF_NAME)
    
    # Generate and validate configurations
    config_manager.generate_confs(save=True)
    config_manager.save_ambari_configurations()
    config_manager.setup_validators()
    config_manager.validate_configurations()
    config_manager.save_ansible_configurations()

    # Example of Docker instance configuration
    """
    docker_instance_num = 4
    parsed_conf = config_manager.sd_conf.get_conf()
    hosts = []
    for i in range(docker_instance_num):
        hosts.append((f"10.10.10.{i}", f"hostname{i}", "password"))
    parsed_conf["hosts"] = hosts
    
    config_manager.sd_conf.set_conf(parsed_conf)
    config_manager.generate_confs(save=True)
    
    advanced_conf = config_manager.advanced_conf
    group_services = advanced_conf.get("group_services")
    hosts_groups = advanced_conf.get("host_groups")
    components_hosts_map = {}
    
    for group_name, services in group_services.items():
        for service in services:
            if service not in components_hosts_map:
                components_hosts_map[service] = []
            components_hosts_map[service].extend(hosts_groups.get(group_name, []))
    
    # Remove duplicates
    for service in components_hosts_map:
        components_hosts_map[service] = list(set(components_hosts_map[service]))
    """
