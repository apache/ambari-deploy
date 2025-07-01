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
Docker Cluster Manager Module

This module provides functionality for managing Docker-based Bigtop Hadoop clusters.
It handles cluster creation, configuration, deployment, and cleanup operations using
Docker containers and docker-compose.
"""

#!/usr/bin/env python3

import argparse
import logging
import os
import random
import re
import shutil
import subprocess
import sys
from concurrent.futures import as_completed, ThreadPoolExecutor
from datetime import datetime

import yaml

from python.common.constants import *


class DockerClusterManager:
    """
    Manager class for Docker-based cluster operations.
    
    This class handles all aspects of Docker cluster management including:
    - Cluster creation and destruction
    - Container configuration and deployment
    - Host configuration and networking
    - Repository setup and environment configuration
    
    Attributes:
        config (dict): Configuration settings for the cluster
        image_name (str): Docker image name for cluster nodes
        provision_id_file (str): File storing the cluster's provision ID
        hosts_file (str): Path to hosts configuration file
        docker_compose_cmd (str): Docker compose command to use
        error_prefix (str): Prefix for error message files
        base_conf (str): Base configuration file name
        docker_compose_env (dict): Environment variables for docker-compose
        head_node (str): ID of the cluster's head node
        docker_compose_dir (str): Directory containing docker-compose files
        components_port_map (dict): Mapping of components to their ports
        repo_local_dir (str): Path to local repository directory
        prj_mount_dir (str): Project mount directory in containers
        shared_dir (str): Shared directory path on host
        container_shared_dir (str): Shared directory path in containers
    """

    def __init__(self, config):
        """
        Initialize the Docker cluster manager.
        
        Args:
            config (dict): Configuration dictionary containing cluster settings
        """
        self.config = config
        self.image_name = self.get_image(
            self.config["distro"]["name"], self.config["distro"]["version"]
        )
        self.prog = os.path.basename(sys.argv[0])
        self.provision_id_file = os.path.join(PRJDIR, ".provision_id")
        self.hosts_file = os.path.join(CONF_DIR, "hosts")
        self.docker_compose_cmd = "docker compose"
        self.error_prefix = ".error_msg_"
        self.base_conf = "base_conf.yml"
        self.setup_logging()
        self.load_config()
        self.docker_compose_env = {}
        self.head_node = None
        self.docker_compose_dir = PRJDIR
        self.components_port_map = self.config["components_port_map"]
        self.repo_local_dir = None

        # Mount points configuration
        self.prj_mount_dir = "/deploy/deploy-home"
        self.shared_dir = os.path.join(PRJDIR, "shared")
        self.container_shared_dir = "/deploy/shared"

    def get_image(self, distro, version):
        """
        Get the appropriate Docker image name based on distribution and version.
        
        Args:
            distro (str): Linux distribution name (e.g., 'centos', 'ubuntu')
            version (str): Distribution version
            
        Returns:
            str: Docker image name
        """
        print(distro, version)
        imagemap = {
            "centos": {
                "7": "bigtop/puppet:trunk-centos-7",
                "8": "bigtop/puppet:trunk-rockylinux-8",
                "9": "bigtop/puppet:trunk-rockylinux-9",
            },
            "ubuntu":{
                "22": "bigtop/puppet:trunk-ubuntu-22.04"
            }
        }
        return imagemap[distro][str(version)]

    def setup_logging(self):
        """
        Configure logging for the cluster manager.
        """
        logging.basicConfig(
            level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s"
        )

    def load_config(self):
        """
        Load and initialize configuration settings.
        
        Sets up basic configuration parameters including:
        - Provision ID
        - Docker image name
        - Memory limits
        - Node list
        - Component list
        """
        logging.info("Loading configuration...")
        self.provision_id = self._load_provision_id()
        self.image_name = self.get_image(
            self.config["distro"]["name"], self.config["distro"]["version"]
        )
        self.memory_limit = self.config["memory_limit"]
        self.nodes = []
        self.components = self.config["components"]
        logging.info("Configuration loaded successfully.")

    def _load_provision_id(self):
        """
        Load the cluster provision ID from file.
        
        Returns:
            str: Provision ID if file exists, None otherwise
        """
        if os.path.exists(self.provision_id_file):
            with open(self.provision_id_file, "r") as f:
                return f.read().strip()
        return None

    def run_command(
        self,
        command,
        workdir=None,
        env_vars=None,
        shell=False,
        logfile=None,
        ignore_errors=False,
    ):
        """
        Execute a shell command with logging and error handling.
        
        Args:
            command: Command to execute (string or list)
            workdir: Working directory for command execution
            env_vars: Environment variables for command
            shell: Whether to run command through shell
            logfile: File to log command output
            ignore_errors: Whether to ignore command failures
            
        Returns:
            tuple: (exit_code, stdout, stderr) or exit_status if logfile provided
            
        Raises:
            Exception: If command fails and ignore_errors is False
        """
        logging.info(f"Executing command: {command}")
        out = logfile or subprocess.PIPE
        env_vars = dict(env_vars) if env_vars else os.environ.copy()
        try:
            process = subprocess.Popen(
                command,
                stdout=out,
                stderr=out,
                shell=shell,
                cwd=workdir,
                env=env_vars,
                universal_newlines=True,
            )

            if logfile:
                exit_status = process.wait()
                return exit_status

            output, error = process.communicate()
            exit_code = process.returncode
            if exit_code == 0:
                logging.info(f"Command executed successfully: {command}")
            else:
                logging.error(
                    f"Command failed with exit code {exit_code}: cmd: {command}, out: {output}, err:{error}"
                )
                if not ignore_errors:
                    raise Exception(
                        f"Command failed with exit code {exit_code}: cmd: {command}, out: {output}, err:{error}"
                    )
            return exit_code, output, error
        except Exception as e:
            logging.error(f"Exception occurred while executing command: {e}")
            if not ignore_errors:
                raise
            return -1, "", str(e)

    def get_result(self, subprocess_res):
        """
        Parse and clean subprocess output.
        
        Args:
            subprocess_res (str): Raw subprocess output
            
        Returns:
            list: List of non-empty output lines
        """
        return [node.strip() for node in subprocess_res.split("\n") if node.strip()]

    def get_nodes(self):
        """
        Retrieve information about cluster nodes.
        
        Updates the nodes list and head_node attributes with
        current container information.
        """
        logging.info("Retrieving node information...")
        if self.provision_id:
            exit_code, output, error = self.run_command(
                f"{self.docker_compose_cmd} -p {self.provision_id} ps -q",
                workdir=self.docker_compose_dir,
                shell=True,
            )
            self.nodes = self.get_result(output)
            self.head_node = self.nodes[0] if self.nodes else None
            logging.info(f"Nodes retrieved: {self.nodes}")

    def create_or_touch_file(self, file_path):
        """
        Create a new file or update timestamp of existing file.
        
        Args:
            file_path (str): Path to the file to create or touch
        """
        logging.info(f"Creating or touching file: {file_path}")
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            print(f"create_or_touch_file  directory {directory}")
            os.makedirs(directory)
        try:
            print(f"create_or_touch_file file_path {file_path}")
            with open(file_path, "a"):
                os.utime(file_path, None)
        except IOError as e:
            logging.error(f"Error creating or touching file: {e}")

    def create(self, num_instances):
        """
        Create a new Docker cluster.
        
        Args:
            num_instances (int): Number of cluster nodes to create
            
        Raises:
            SystemExit: If cluster already exists
        """
        logging.info(f"Creating cluster with {num_instances} instances...")
        if os.path.exists(self.provision_id_file):
            logging.error(
                f"Cluster already exists! Run ./{self.prog} -d to destroy the cluster or delete {self.provision_id_file} file and containers manually."
            )
            sys.exit(1)
        self.provision_id = (
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_r{random.randint(1000, 9999)}"
        )
        self.create_or_touch_file(self.hosts_file)
        
        # Create shared directory
        if not os.path.exists(self.shared_dir):
            os.makedirs(self.shared_dir)

        self.run_command(
            f"{self.docker_compose_cmd} -p {self.provision_id} up -d  --no-recreate",
            workdir=self.docker_compose_dir,
            shell=True,
            env_vars=self.docker_compose_env,
        )
        with open(self.provision_id_file, "w") as f:
            f.write(self.provision_id)

        self.get_nodes()
        logging.info("Cluster creation completed.")

    def install_cluster(self):
        """
        Configure and install the cluster software.
        
        This method:
        1. Generates hosts file
        2. Sets up cluster environment
        3. Deploys the cluster software
        """
        logging.info("Configuring cluster...")
        self.generate_hosts()
        self.setup_cluster_env()
        self.deploy_cluster()
        logging.info("Cluster configuration completed.")

    def generate_hosts(self):
        """
        Generate hosts file for cluster nodes.
        
        Creates and configures /etc/hosts entries for all cluster nodes.
        """
        logging.info("Generating hosts file...")
        self._remove_file(self.hosts_file)
        for node in self.nodes:
            exit_code, output, error = self.run_command(
                f"docker inspect --format '{{{{range.NetworkSettings.Networks}}}}{{{{.IPAddress}}}}{{{{end}}}} {{{{.Config.Hostname}}}}.{{{{.Config.Domainname}}}} {{{{.Config.Hostname}}}}' {node}",
                shell=True,
            )
            entry = self.get_result(output)[0]
            self.run_command(
                f'docker exec {self.head_node} bash -c "echo {entry} >> /etc/hosts"',
                shell=True,
            )
        self.run_command(
            f"docker exec {self.head_node} bash -c \"echo '127.0.0.1 localhost' >> /etc/hosts\"",
            shell=True,
        )
        logging.info("Hosts file generated successfully.")

    def setup_cluster_env(self):
        """
        Set up the cluster environment.
        
        Bootstraps nodes with necessary environment configuration
        using distribution-specific setup scripts.
        """
        distro = self.config["distro"]["name"]
        logging.info(f"Bootstrapping nodes with distro: {distro}")

        default_password = self.config["default_password"]
        commands = [
            f"docker exec {node} bash -c '{self.prj_mount_dir}/{SHELL_UTILS_RELATIVE_PATH}/setup-env-{distro}.sh true \"{default_password}\" 2>&1 | tee {self.prj_mount_dir}/logs/setup-env-{node}.log'"
            for node in self.nodes
        ]
        self.parallel_execute(
            self.run_command, commands, env_vars=self.docker_compose_env, shell=True
        )

        logging.info("Bootstrap completed.")

    def parallel_execute(self, task, params, **kwargs):
        """
        Execute multiple tasks in parallel.
        
        Args:
            task: Function to execute
            params: List of parameters for each task execution
            **kwargs: Additional keyword arguments for task execution
        """
        logging.info(f"Executing {len(params)} tasks in parallel...")
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(task, param, **kwargs): param for param in params
            }

            for future in as_completed(futures):
                param = futures[future]
                try:
                    result = future.result()
                    if result:
                        logging.info(f"Task executed successfully: {param}")
                    else:
                        logging.warning(f"Task execution failed: {param}")
                except Exception as e:
                    logging.error(
                        f"Task execution resulted in an exception: {param}. Error: {e}"
                    )
        logging.info("Parallel execution completed.")

    def deploy_cluster(self):
        """
        Deploy the cluster software stack.
        
        Executes the cluster installation script on the head node.
        """
        logging.info("Generating configuration file...")
        dest_dir = self.prj_mount_dir
        conf_dir = f"{self.prj_mount_dir}/conf"
        self.run_command(
            f"docker exec {self.head_node} bash -c '{self.prj_mount_dir}/{SHELL_UTILS_RELATIVE_PATH}/install_cluster.sh {dest_dir} true'",
            shell=True,
        )

    def get_hosts_config(self):
        """
        Get host configuration information for all cluster nodes.
        
        Returns:
            list: List of tuples containing (ip, hostname, password) for each node
        """
        hosts = []
        for node in self.nodes:
            exit_code, output, error = self.run_command(
                f"docker inspect --format '{{{{range.NetworkSettings.Networks}}}}{{{{.IPAddress}}}}{{{{end}}}} {{{{.Config.Hostname}}}}.{{{{.Config.Domainname}}}}' {node}",
                shell=True,
            )
            ip_hostname = self.get_result(output)[0]
            ip_hostname_arr = re.split(r"\s+", ip_hostname.strip())
            hosts.append((ip_hostname_arr[0], ip_hostname_arr[1], "B767610qa4Z"))
        return hosts

    def destroy(self):
        """
        Destroy the cluster and clean up resources.
        
        This method:
        1. Stops and removes containers
        2. Removes network
        3. Cleans up configuration files
        4. Removes shared directory
        """
        logging.info("Destroying cluster...")
        if not self.provision_id:
            logging.info("No cluster exists!")
            return

        self.get_nodes()
        if not self.nodes:
            self._remove_provision_id_file()
            return

        self._cleanup_head_node()
        self._stop_and_remove_containers()
        self._remove_network()
        self._remove_files()
        
        # Clean up shared directory
        if os.path.exists(self.shared_dir):
            shutil.rmtree(self.shared_dir)
            
        logging.info("Cluster destroyed successfully.")

    def _cleanup_head_node(self):
        """
        Clean up the head node configuration.
        """
        if self.nodes:
            print("pass")

    def _stop_and_remove_containers(self):
        """
        Stop and remove all cluster containers.
        """
        if self.provision_id:
            self.run_command(
                f"{self.docker_compose_cmd} -p {self.provision_id} stop",
                workdir=self.docker_compose_dir,
                env_vars=self.docker_compose_env,
                shell=True,
            )
            self.run_command(
                f"{self.docker_compose_cmd} -p {self.provision_id} rm -f",
                workdir=self.docker_compose_dir,
                env_vars=self.docker_compose_env,
                shell=True,
            )

    def _remove_network(self):
        """
        Remove the cluster's Docker network.
        """
        network_id = self.run_command(
            f"docker network ls --quiet --filter name={self.provision_id}_default",
            env_vars=self.docker_compose_env,
            shell=True,
        )
        if network_id:
            self.run_command(
                f"docker network rm {self.provision_id}_default",
                env_vars=self.docker_compose_env,
                shell=True,
            )

    def _remove_files(self):
        """
        Remove all cluster-related files.
        """
        for file in [self.hosts_file, self.provision_id_file] + [
            f for f in os.listdir(".") if f.startswith(self.error_prefix)
        ]:
            self._remove_file(file)

    def _remove_file(self, file):
        """
        Remove a file or directory.
        
        Args:
            file (str): Path to file or directory to remove
        """
        print(f"remove file {file}")
        if os.path.isdir(file):
            shutil.rmtree(file, ignore_errors=True)
        elif os.path.exists(file):
            os.remove(file)

    def _remove_provision_id_file(self):
        """
        Remove the provision ID file.
        """
        if os.path.exists(self.provision_id_file):
            os.remove(self.provision_id_file)

    def execute(self, target, *args):
        """
        Execute a command on a specific cluster node.
        
        Args:
            target: Node identifier (index or name)
            *args: Command and arguments to execute
        """
        logging.info(f"Executing command on target: {target}")
        if target.isdigit():
            self.get_nodes()
            node = self.nodes[int(target) - 1]
        else:
            node = target
        self.run_command(f"docker exec -ti {node} {' '.join(args)}", shell=True)

    def env_check(self):
        """
        Check the environment for required dependencies.
        
        Verifies Docker and docker-compose are installed and accessible.
        """
        logging.info("Performing environment check...")
        logging.info("Checking docker:")
        self.run_command("docker -v", shell=True)
        logging.info("Checking docker-compose:")
        self.run_command(
            f"{self.docker_compose_cmd} -v", workdir=self.docker_compose_dir, shell=True
        )

    def list_cluster(self):
        """
        List the status of all cluster containers.
        """
        logging.info("Listing cluster status...")
        try:
            exit_code, output, error = self.run_command(
                f"{self.docker_compose_cmd} -p {self.provision_id} ps",
                workdir=self.docker_compose_dir,
                shell=True,
            )
            msg = self.get_result(output)
        except subprocess.CalledProcessError:
            msg = ["Cluster hasn't been created yet."]

        for info in msg:
            logging.info(info)

    def generate_compose(self, components_ports, compose_file_path, hosts):
        """
        Generate docker-compose.yml file for the cluster.
        
        Args:
            components_ports (dict): Mapping of components to their port configurations
            compose_file_path (str): Path where docker-compose.yml will be written
            hosts (list): List of host configurations
        """
        mapped_ports = set()

        def get_ports_by_host(components_ports, hostname):
            """
            Get port mappings for a specific host.
            
            Args:
                components_ports (dict): Component to ports mapping
                hostname (str): Host to get ports for
                
            Returns:
                list: List of port mappings for the host
            """
            components_port_map_table = self.components_port_map
            ports = []
            for component, hosts in components_ports.items():
                if hostname in hosts and component in components_port_map_table:
                    port = components_port_map_table[component]
                    if port not in mapped_ports:
                        mapped_ports.add(port)
                        ports.append(f"{port}:{port}")
            return ports

        services = {}

        # Create service configuration for each host
        for i, hostname, passwd in hosts:
            service_name = f"bigtop_{hostname}"
            volumes = [
                f"{PRJDIR}:{self.prj_mount_dir}",
                f"{CONF_DIR}/hosts:/etc/hosts",
                f"{self.prj_mount_dir}/bin",
                f"{self.shared_dir}:{self.container_shared_dir}"
            ]
            
            # Add repository volume mount if configured
            if self.repo_local_dir:
                volumes.append(f"{self.repo_local_dir}:{self.repo_local_dir}")

            services[service_name] = {
                "image": f"{self.image_name}",
                "mem_swappiness": 0,
                "command": "/sbin/init",
                "domainname": "bigtop.apache.org",
                "privileged": True,
                "mem_limit": f"{self.memory_limit}",
                "volumes": volumes,
                "ports": get_ports_by_host(components_ports, hostname),
            }

        compose = {"services": services}

        with open(compose_file_path, "w") as file:
            yaml.dump(compose, file)

        print(f"Generated docker-compose file: {compose_file_path}")

    def get_deploy_host_ip(self):
        """
        Get the IP address of the host machine running the deployment script.
        Uses the first container's hostname to get its IP address.
        
        Returns:
            str: IP address of the deployment host
        """
        self.get_nodes()
        if self.nodes:
            exit_code, output, error = self.run_command(
                f"docker inspect --format '{{{{range.NetworkSettings.Networks}}}}{{{{.IPAddress}}}}{{{{end}}}}' {self.nodes[0]}",
                shell=True
            )
            return output.strip()
        return "127.0.0.1"


def main():
    """
    Main entry point for command-line interface.
    """
    manager = DockerClusterManager()

    parser = argparse.ArgumentParser(
        description="Manage Docker based Bigtop Hadoop cluster"
    )
    parser.add_argument(
        "-c",
        "--create",
        type=int,
        metavar="NUM_INSTANCES",
        help="Create a Docker based Bigtop Hadoop cluster",
    )
    parser.add_argument(
        "-d", "--destroy", action="store_true", help="Destroy the cluster"
    )
    parser.add_argument(
        "-dcp",
        "--docker-compose-plugin",
        action="store_true",
        help="Execute docker compose plugin command 'docker compose'",
    )

    args = parser.parse_args()

    logging.info(f"Parsed arguments: {args}")

    manager.initialize_config(args)
    if args.create:
        manager.env_check()
        manager.create(args.create)


if __name__ == "__main__":
    main()

# First generate cluster topology, then get machines that need port mapping, then dynamically generate to docker-compose
