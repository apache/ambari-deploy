# Automated Deployment Guide

This guide provides detailed instructions for automated deployment of Apache Ambari and Hadoop ecosystem components using both Docker and bare metal/VM approaches.

## Overview

The automated deployment script supports two deployment modes:

1. **Docker Deployment**: Quick one-click deployment of a Hadoop cluster for testing, development environment, or demo purposes.
   - Fastest way to get a working cluster
   - Minimal configuration required
   - Perfect for development and testing
   - Automatic container orchestration
   - Easy cleanup and redeployment

2. **Bare Metal/VM Deployment**: Production-ready automated deployment that supports both one-click installation and advanced customization options, such as adjusting cluster topology, component placement, external database integration, and data directory configuration.

## Prerequisites

### For Bare Metal/VM Deployment

1. **YUM Repository Configuration**
   - Ensure all machines have properly configured YUM repositories (base and dev repositories must be available)
   - Install Ansible dependencies by running:
   ```bash
   sh deploy_py/shell/utils/setup-env-centos.sh false
   ```

2. **SSH Configuration (Rocky 9)**
   - Modify sshd configuration on all nodes:
   ```bash
   vi /etc/ssh/sshd_config
   # Change these settings:
   PasswordAuthentication yes  # Make sure there's only one instance of this setting
   PermitRootLogin yes        # Ensure this exists and is uncommented
   
   # Restart sshd
   systemctl restart sshd.service
   
   # Test SSH connectivity
   ssh root@<hostname>  # Verify password login works
   ```

3. **Firewall and SELinux Configuration**
   
   For RHEL 7, Rocky Linux 8/9:
   ```bash
   # Disable firewall
   systemctl stop firewalld
   systemctl disable firewalld
   systemctl status firewalld
   
   # Disable SELinux temporarily
   setenforce 0
   
   # Disable SELinux permanently (requires reboot)
   sed -i 's/SELINUX=enforcing/SELINUX=disabled/' /etc/selinux/config
   ```

   Verify status:
   ```bash
   # Check firewall status
   systemctl status firewalld
   
   # Check SELinux status
   getenforce
   # or
   sestatus
   ```

4. **Hostname Configuration**
   - Ensure all machines have unique and properly formatted hostnames
   - Edit /etc/hostname and reboot if changes are made:
   ```bash
   vi /etc/hostname
   # Edit hostname
   reboot
   ```

### For Docker Deployment

Docker deployment uses Apache Bigtop puppet containers. This is the quickest way to get a working cluster up and running.

1. Update base images with dependencies (one-time setup):
   ```bash
   cd deploy_py/shell/utils/
   # For Rocky 8
   chmod +x ./update_bigtop_image.sh && ./update_bigtop_image.sh rocky8
   
   # For Rocky 9
   chmod +x ./update_bigtop_image.sh && ./update_bigtop_image.sh rocky9
   ```

2. **Quick Start Configuration**
   
   For Docker deployment, you only need to modify a few essential parameters in `base_conf.yml`:

   ```yaml
   # Local package directory path (where you placed the downloaded packages)
   repo_pkgs_dir: "/data1/apache/ambari-3.0_pkgs"
   
   # Components you want to install
   components_to_install: ["hbase","hdfs","yarn","hive","zookeeper","ambari"]
   
   # Docker resource allocation
   docker_options:
     instance_num: 4  # Number of containers
     memory_limit: "16g"  # Memory per container
     components_port_map:
       AMBARI_SERVER: 8083  # Port for accessing Ambari UI
   ```

   Other configurations can be left as default for initial testing, and can be customized later based on your needs.

3. **Deploy**
   ```bash
   source setup_pypath.sh
   python3 deploy_py/main.py -docker-deploy
   ```

   That's it! The script will automatically:
   - Create and configure containers
   - Set up networking
   - Install selected components
   - Configure the cluster
   
   You can monitor the deployment progress at `http://localhost:8083` (or whatever port you configured for AMBARI_SERVER).

## Installation Package Setup

1. Download Ambari and Hadoop ecosystem packages from:
   https://ambari.apache.org/docs/3.0.0/quick-start/download

2. Place all packages in a fixed directory (e.g., /data1/ambari/)

3. Ensure directory permissions:
   ```bash
   chmod 755 /data1/ambari
   chmod 755 /data1
   ```

## Deployment Configuration

1. **Initialize Configuration**
   ```bash
   cd bigdata-deploy
   cp conf/base_conf.yml.template conf/base_conf.yml
   ```

2. **Configuration Complexity**

   - **For Docker Deployment**: Only requires minimal configuration:
     - `repo_pkgs_dir`: Location of installation packages
     - `components_to_install`: Components you want to install
     - `docker_options`: Resource limits and port mappings
     - Other settings can use defaults for testing

   - **For Bare Metal/VM Deployment**: Requires more detailed configuration:
     - Host information
     - Network settings
     - Storage configuration
     - Security settings
     - etc.

3. **Configure base_conf.yml**

   Below is a comprehensive explanation of all configuration parameters:

   ```yaml
   # Default password for all services (used for Ambari Web UI, database access, etc.)
   default_password: 'B767610qa4Z'
   
   # Data directories for Hadoop components
   # Multiple directories can be specified for HDFS DataNode storage
   # Example: ["/data/sdv1", "/data/sdv2"]
   # Ensure all nodes have these directories available
   data_dirs: ["/data/sdv1"]
   
   # Repository configuration
   # Two options available:
   # 1. Use existing repository:
   repos:
     - {"name": "ambari_repo", "url": "http://server0:8881/repository/yum/udh3/"}
   
   # 2. Use local package directory (script will create repo automatically):
   repos:
     - {"name": "ambari_repo", "url": "file:///data1/apache/ambari-3.0_pkgs"}
   
   # Local package directory path (used when creating local repo)
   repo_pkgs_dir: "/data1/apache/ambari-3.0_pkgs"
   
   # Host configuration (not needed for Docker deployment)
   # Format: IP_ADDRESS HOSTNAME PASSWORD
   # Can use ansible-style expressions for multiple hosts
   hosts:
   # Single host entry:
   - 192.168.56.10 vm1 B767610qa4Z
   # Multiple hosts using range:
   - 10.1.1.1[0-4] server[0-4] password
   
   # Deployment user (must have sudo privileges)
   # Recommended to use root, otherwise ensure user has sudo access
   user: root
   
   # Ambari Stack version
   stack_version: '3.3.0'
   
   # Components to install
   # Available components:
   # - Basic cluster: ["ambari", "hdfs", "zookeeper", "yarn"]
   # - Full stack: ["hbase","hdfs","yarn","hive","zookeeper","kafka","spark",
   #               "flink","ranger","infra_solr","ambari","ambari_metrics",
   #               "kerberos","alluxio"]
   components_to_install: ["hbase","hdfs","yarn","hive","zookeeper","ambari"]
   
   # Cluster name (avoid special characters)
   cluster_name: 'cluster'
   
   # HDFS HA name configuration
   hdfs_ha_name: 'ambari-cluster'
   
   # SSH port for ansible deployment
   # Change if using non-standard SSH port
   ansible_ssh_port: 22
   
   # Ambari Server port configuration
   ambari_server_port: 8080
   
   # Docker deployment specific options
   docker_options:
     # Number of docker containers (minimum 3)
     instance_num: 4
     
     # Memory limit per container
     memory_limit: "16g"
     
     # Port mapping for accessing services from host
     # Format: COMPONENT_NAME: HOST_PORT
     components_port_map:
       AMBARI_SERVER: 8083
       # Optional mappings:
       # NAMENODE: 50070
       # RESOURCEMANAGER: 8088
       # HBASE_MASTER: 16010
       # FLINK_HISTORYSERVER: 8082
       # RANGER_ADMIN: 6080
     
     # Container distribution configuration
     distro:
       # Options: "centos" or "ubuntu"
       name: "centos"
       # For CentOS: 8 or 9
       # For Ubuntu: 22 or 24 (package support pending)
       version: 8
   
   # Component memory configurations (in MB)
   # Adjust based on your resource availability
   # These are initial values, can be modified later in Ambari UI
   hbase_heapsize: 1024
   hadoop_heapsize: 1024
   hive_heapsize: 1024
   infra_solr_memory: 1024
   spark_daemon_memory: 1024
   zookeeper_heapsize: 1024
   yarn_heapsize: 1024
   alluxio_memory: 1024
   ```

3. **Configuration Notes**

   - **Repository Setup**: 
     - For production environments, it's recommended to set up a proper HTTP repository
     - For testing, the automatic local repository creation is sufficient
   
   - **Host Configuration**:
     - Ensure all hostnames are unique and properly formatted
     - Password must be accessible for the specified user
     - For large clusters, use range notation to simplify configuration
   
   - **Component Selection**:
     - Start with basic components for initial testing
     - Add additional components based on your needs
     - Ensure dependencies are considered (e.g., Ranger requires Infra Solr)
   
   - **Memory Configuration**:
     - Default values are conservative
     - For production, adjust based on your hardware specifications
     - Consider total memory available when configuring multiple components
   
   - **Docker Deployment**:
     - Port mapping is optional but useful for external access
     - Memory limits should account for host system resources
     - Instance number should be at least 3 for HA features

## Deployment Process

### For Bare Metal/VM Deployment

1. **Setup Python Environment**
   ```bash
   source setup_pypath.sh
   ```

2. **Generate Deployment Configuration**
   ```bash
   python3 deploy_py/main.py -generate-conf
   ```

3. **Start Deployment**
   ```bash
   nohup python3 deploy_py/main.py -deploy &
   tail -f logs/ansible-playbook.log
   ```

### For Docker Deployment

1. **Setup and Deploy**
   ```bash
   source setup_pypath.sh
   python3 deploy_py/main.py -docker-deploy
   ```

## Troubleshooting

### Ambari Agent Registration Issues

If Ambari agents fail to register, verify hostname configuration:

```python
python3
import socket
socket.getfqdn()
```

Ensure the output matches the hostname configured in:
- Automated installation script
- /etc/hosts file
- Actual machine hostname

## Monitoring Deployment

Access the Ambari Web UI at `http://<AMBARI_SERVER>:8080` to monitor deployment progress.

Default credentials:
- Username: admin
- Password: (value of default_password in configuration)

## Advanced Configuration

For advanced deployment scenarios such as:
- Customizing cluster topology
- Using external databases
- Configuring custom directories
- Enabling Ranger
- Customizing Ambari settings

Please refer to our [**Advanced Deployment Guide**](advanced-deployment.md). 