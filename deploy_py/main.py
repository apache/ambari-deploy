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

#!/usr/bin/python3
# -*- coding:utf8 -*-

"""
Main entry point for the cluster deployment system.
This module provides the core functionality for deploying clusters in both Docker and bare metal/KVM environments.

The system supports two deployment modes:
1. Regular deployment (bare metal/KVM)
2. Docker-based deployment

Key features:
- Configuration management
- Multiple deployment modes
- Automated environment setup
- Cluster service configuration
"""

import argparse
import os

from python.common.basic_logger import get_logger
from python.common.constants import *
from python.common.path_manager import *
from python.deploy.deployment import *
from python.executor.command_executor import *

# Initialize logger for the main application
logger = get_logger()


class MainApplication:
    """
    Main application class that orchestrates the deployment process.
    
    This class is responsible for:
    - Parsing command line arguments
    - Managing deployment modes
    - Coordinating configuration generation
    - Executing deployment workflows
    
    Attributes:
        args: Parsed command line arguments
        os_info: Tuple containing OS information (type, version, architecture)
        path_manager: Manager for handling file paths
        deployment_manager: Manager for deployment operations
        executor: Command execution handler
    """

    def __init__(self):
        """
        Initialize the main application with necessary components.
        Sets up argument parsing, OS information, and managers for deployment.
        """
        self.args = self.parse_arguments()
        self.os_info = self.get_os_info_tuple()
        self.path_manager = PathManager()
        self.deployment_manager = Deployment()
        self.executor = CommandExecutor

    def get_os_info_tuple(self):
        """
        Parse and return OS information as a tuple.
        
        Returns:
            tuple: Contains (os_type, os_version, os_architecture)
            If no OS info provided, returns empty strings
        """
        os_info_arr = (
            self.args.os_info.split(",") if self.args.os_info else ["", "", ""]
        )
        return tuple(os_info_arr)

    def initialize(self):
        """
        Initialize the application environment.
        Currently a placeholder for future initialization needs.
        """
        pass
        # FilesystemUtil.create_dir(OUTPUT_DIR, empty_if_exists=True)

    def check_os_info(self):
        """
        Validate the OS information against supported configurations.
        
        Raises:
            AssertionError: If OS type or architecture is not supported
        """
        os_type, os_version, os_arch = self.os_info
        assert os_arch in SUPPORTED_ARCHS
        assert os_type in SUPPORTED_OS

    def parse_arguments(self):
        """
        Parse command line arguments for deployment configuration.
        
        Supported arguments:
        - deploy: Regular cluster deployment
        - docker-deploy: Docker-based deployment
        - generate-conf: Generate configuration files
        - is-docker: Whether running in Docker environment
        - os-info: Operating system information
        - docker-instance-num: Number of Docker instances
        
        Returns:
            argparse.Namespace: Parsed command line arguments
        """
        parser = argparse.ArgumentParser(description="Cluster Deployment Tool.")
        parser.add_argument("-deploy", action="store_true", help="Deploy a cluster")
        parser.add_argument(
            "-docker-deploy", action="store_true", help="Deploy a cluster using Docker"
        )
        parser.add_argument(
            "-generate-conf",
            action="store_true",
            help="Generate all configuration files",
        )
        parser.add_argument(
            "--is-docker",
            dest="is_docker",
            type=bool,
            default=False,
            help="Whether running in Docker environment (true/false)",
        )
        parser.add_argument(
            "-os-info",
            metavar="os_info",
            type=str,
            default="",
            help="Release parameters: os_name,os_version,arch (e.g., centos,7,x86_64)",
        )
        parser.add_argument(
            "-n",
            "--docker-instance-num",
            dest="docker_instance_num",
            type=int,
            help="Number of Docker instances for deployment",
        )

        args = parser.parse_args()
        print(args)
        return args

    def deploy_cluster_if_needed(self):
        """
        Execute cluster deployment based on specified mode.
        
        If -deploy flag is set: Execute regular deployment
        If -docker-deploy flag is set: Execute Docker-based deployment
        """
        if self.args.deploy:
            if not self.args.is_docker:
                self.clear_logs()
            self.deployment_manager.deploy_cluster(self.args.is_docker)
        elif self.args.docker_deploy:
            self.clear_logs()
            self.deployment_manager.deploy_cluster_by_docker(
                self.args.docker_instance_num
            )

    def generate_conf_if_needed(self):
        """
        Generate configuration files if requested.
        
        If -generate-conf flag is set:
        - Generates detailed configuration from base configuration
        - Creates necessary deployment templates
        """
        if self.args.generate_conf:
            self.deployment_manager.generate_deploy_conf()

    def run(self):
        """
        Main execution method for the deployment process.
        
        Workflow:
        1. Initialize the environment
        2. Deploy cluster if requested
        3. Generate configuration if requested
        """
        self.initialize()
        self.deploy_cluster_if_needed()
        self.generate_conf_if_needed()

    def clear_logs(self):
        """
        Clear all contents in the logs directory under project root.
        """
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        if os.path.exists(log_dir):
            for file in os.listdir(log_dir):
                os.remove(os.path.join(log_dir, file))


def check_config():
    """
    Placeholder for configuration validation.
    To be implemented with specific validation rules.
    """
    pass


if __name__ == "__main__":
    # Create and run the main application
    app = MainApplication()
    app.run()


# Required dependencies:
# pip3 install pyyaml
# pip3 install docker
# pip3 install jinja2