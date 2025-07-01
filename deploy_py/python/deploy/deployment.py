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
Deployment Module

This module provides the core functionality for deploying clusters using Ansible playbooks.
It handles both standard deployments and Docker-based deployments, managing the entire
deployment lifecycle from configuration to execution.
"""

# -*- coding:utf8 -*-
# !/usr/bin/python3
import os
import shutil
from pathlib import Path

from python.common.basic_logger import get_logger
from python.common.constants import *
from python.config_management.configuration_manager import *
from python.deploy.docker_cluster_manager import *
from python.executor.command_executor import *
from python.utils.os_utils import *

logger = get_logger()


class Deployment:
    """
    Main deployment orchestrator class.
    
    This class manages the deployment process for clusters, handling both
    standard and Docker-based deployments. It coordinates configuration
    management, playbook execution, and repository setup.
    
    Attributes:
        prepare_nodes_only (bool): Flag to only prepare nodes without full deployment
        executor: Command execution utility class
        conf_manager: Configuration management instance
        log_file (str): Path to the Ansible playbook log file
    """
    
    def __init__(self, prepare_nodes_only=False):
        """
        Initialize the deployment manager.
        
        Args:
            prepare_nodes_only (bool): If True, only prepare nodes without full deployment
        """
        self.prepare_nodes_only = prepare_nodes_only
        self.executor = CommandExecutor
        self.conf_manager = ConfigurationManager(BASE_CONF_NAME)
        self.log_file = os.path.join(LOGS_DIR, "ansible_playbook.log")

    def all_tasks(self):
        """
        Get the list of all deployment tasks.
        
        Returns:
            list: List of Ansible playbook names in deployment order
        """
        return [
            "prepare_nodes.yml",
            "install_ambari.yml",
            "configure_ambari.yml",
            "apply_blueprint.yml",
            "post_install.yml",
        ]

    def generate_deploy_tasks(self):
        """
        Generate the list of deployment tasks based on configuration.
        
        Determines which playbooks to run based on:
        - Whether only Ambari is being installed
        - Whether only node preparation is needed
        - Full deployment requirements
        
        Returns:
            list: List of full paths to Ansible playbooks to execute
        """
        install_ambari_only = len(self.conf_manager.sd_conf.get("components_to_install")) == 1 and self.conf_manager.sd_conf.get("components_to_install")[0] == "ambari"
        if install_ambari_only:
            playbook_tasks = [
                task for task in self.all_tasks() if task != "apply_blueprint.yml"
            ]
        elif self.prepare_nodes_only:
            playbook_tasks = [self.all_tasks()[0]]
        else:
            playbook_tasks = self.all_tasks()
        print(playbook_tasks)
        return [
            os.path.join(ANSIBLE_PRJ_DIR, f"playbooks/{task}")
            for task in playbook_tasks
        ]

    def execute_tasks(self, playbook_tasks):
        """
        Execute the specified Ansible playbook tasks.
        
        Args:
            playbook_tasks (list): List of playbook paths to execute
            
        Raises:
            Exception: If cluster deployment fails
        """
        inventory_path = os.path.join(ANSIBLE_PRJ_DIR, "inventory/hosts")
        env_vars = os.environ.copy()
        for playbook_path in playbook_tasks:
            command = [
                f"ansible-playbook",
                playbook_path,
                f"--inventory={inventory_path}",
            ]
            exit_status = self.executor.execute_command_withlog(
                command, self.log_file, workdir=PRJDIR, env_vars=env_vars
            )
            logger.info(f"run_playbook {command} exit_status: {exit_status}")
            if exit_status == 0:
                logger.info("Cluster deployed successfully")
            else:
                logger.error("Cluster deployment failed")
                raise Exception("Cluster deployment failed, check the log")

    def deploy_cluster(self, is_docker=False):
        """
        Deploy a cluster using standard deployment process.
        
        This method:
        1. Loads and validates configurations
        2. Sets up local repository if needed
        3. Executes deployment tasks
        
        Args:
            is_docker (str): Flag indicating if deployment is Docker-based
            
        Raises:
            Exception: If no Ambari repository is configured
        """
        conf_manager = self.conf_manager
        conf_manager.load_confs()

        print(f"deploy_cluster {is_docker}")
        if not is_docker:
            # Docker has already generated configuration, skip
            conf_manager.save_ambari_configurations()
            conf_manager.setup_validators()
            conf_manager.validate_configurations()
            conf_manager.save_ansible_configurations()


        # Check if either HTTP or file repo is configured
        if not conf_manager.has_any_ambari_repo() and not conf_manager.has_repo_pkgs():
            raise Exception("No Ambari repository configured. Please configure either HTTP or file repository.")
        
        # Setup local repo only if using local repository
        if conf_manager.has_repo_pkgs():
            self.setup_repo()

        self.prepare_nodes_only = conf_manager.advanced_conf.get("prepare_nodes_only")
        self.execute_tasks(self.generate_deploy_tasks())

    def deploy_cluster_by_docker(self, docker_instance_num, is_ci=False):
        """
        Deploy a cluster using Docker containers.
        
        This method:
        1. Determines node count and components to deploy
        2. Generates Docker compose configuration
        3. Starts Docker cluster
        4. Updates configuration with Docker hosts
        5. Deploys the cluster
        
        Args:
            docker_instance_num (int): Number of Docker instances to deploy
            is_ci (bool): Flag indicating if running in CI environment
        """
        # Load base configuration and generate initial hosts
        conf_manager = self.conf_manager
        parsed_conf = conf_manager.sd_conf.get_conf()
        docker_confg = parsed_conf["docker_options"]
        docker_confg["components"] = parsed_conf["components_to_install"]
        docker_confg["default_password"] = parsed_conf["default_password"]

        if not docker_instance_num:
            docker_instance_num = parsed_conf["docker_options"]["instance_num"]
        logger.info(f"Number of Docker instances to deploy: {docker_instance_num}")

        # Initialize configuration with temporary IPs for initial conf generation
        hosts = []
        for i in range(docker_instance_num):
            hosts.append((f"10.10.10.{i}", f"hostname{i}", "password"))
        parsed_conf["hosts"] = hosts

        # Generate initial configuration with basic settings
        conf_manager.sd_conf.set_conf(parsed_conf)
        conf_manager.generate_confs(save=True)

        # Get component to host mapping
        logger.info("Retrieving machine port mapping.")
        advanced_conf = conf_manager.advanced_conf
        components_hosts_map = self.get_components_hosts_map(
            advanced_conf.get("group_services"), advanced_conf.get("host_groups")
        )
        logger.info(f"Components to hosts map: {components_hosts_map}")

        # Setup and deploy Docker cluster
        logger.info("Generating docker-compose.yml.")
        dk = DockerClusterManager(docker_confg)

        if conf_manager.has_repo_pkgs():
            dk.repo_local_dir = self.conf_manager.advanced_conf.get("repo_pkgs_dir", "")

        # Generate and deploy Docker compose configuration
        dk.generate_compose(
            components_hosts_map, os.path.join(PRJDIR, "docker-compose.yml"), hosts
        )

        logger.info("Deploying Docker cluster.")
        dk.env_check()
        dk.destroy()
        dk.create(docker_instance_num)

        # Update configuration with actual Docker container IPs
        logger.info("Updating configuration with Docker hosts.")
        docker_hosts_config = dk.get_hosts_config()
        logger.info(f"Docker hosts configuration: {docker_hosts_config}")

        # After Docker cluster creation
        parsed_conf["hosts"] = docker_hosts_config
        parsed_conf["skip_cluster_clear"] = True
        parsed_conf["local_repo_ipaddress"] = dk.get_deploy_host_ip()

        # Update configuration after Docker cluster creation
        conf_manager.sd_conf.set_conf(parsed_conf)
        conf_manager.generate_confs(save=True)

        # Load and validate updated configuration
        conf_manager.load_confs()
        conf_manager.save_ambari_configurations()
        conf_manager.setup_validators()
        conf_manager.validate_configurations()
        conf_manager.save_ansible_configurations()

        logger.info("Installing cluster...")
        dk.install_cluster()

    def get_components_hosts_map(self, group_services, hosts_groups):
        """
        Generate mapping between components and their host assignments.
        
        Args:
            group_services (dict): Mapping of groups to their services
            hosts_groups (dict): Mapping of groups to their hosts
            
        Returns:
            dict: Mapping of components to their assigned hosts
        """
        components_hosts_map = {}
        for group_name, services in group_services.items():
            for service in services:
                if service not in components_hosts_map:
                    components_hosts_map[service] = []
                components_hosts_map[service].extend(hosts_groups.get(group_name, []))

        # Remove duplicate host assignments
        for service in components_hosts_map:
            components_hosts_map[service] = list(set(components_hosts_map[service]))
        print(components_hosts_map)
        return components_hosts_map

    def generate_deploy_conf(self):
        """
        Generate deployment configuration files.
        """
        self.conf_manager.generate_confs(save=True)

    def setup_repo(self):
        """
        Set up the local software package repository.
        Raises:
            Exception: If repository setup fails or required files are missing
        """
        if self.conf_manager.has_repo_pkgs() and  self.conf_manager.has_any_ambari_repo():
            raise Exception("Should not setup repo_pkgs_dir when using HTTP repo")

        local_repo_path = self.conf_manager.advanced_conf.get("repo_pkgs_dir", "")
        if not local_repo_path:
            raise Exception("File repository path not found in configuration")

        create_http_repo_for_local_pkgs = self.conf_manager.advanced_conf.get("create_http_repo_for_local_pkgs", False)

        # Execute setup_repo.sh script
        setup_repo_script = os.path.join(SHELL_UTILS_PATH, "setup_repo.sh")
        if not os.path.exists(setup_repo_script):
            raise Exception(f"Setup repo script not found at {setup_repo_script}")

        # Get current OS type
        os_type = get_os_type()

        http_repo_port = self.conf_manager.advanced_conf.get("http_repo_port", 8881)
        
        # Execute script
        command = [setup_repo_script, local_repo_path, str(create_http_repo_for_local_pkgs).lower(),str(http_repo_port), os_type]
        exit_status = self.executor.execute_command_withlog(
            command, self.log_file, workdir=PRJDIR
        )
        
        if exit_status != 0:
            raise Exception("Failed to setup repository, check the log for details")
