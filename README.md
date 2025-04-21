# Apache Ambari Automated Deployment

A comprehensive automation tool for deploying Apache Ambari and Hadoop ecosystem components, supporting both Docker-based development environments and production-grade bare metal/VM deployments.

## Features

- **Flexible Deployment Options**
  - Docker-based deployment for development and testing
  - Bare metal/VM deployment for production environments
  - Support for high availability (HA) configurations

- **Component Support**
  - Core Components: HDFS, YARN, ZooKeeper
  - Processing: Hive, Spark, Flink
  - Storage: HBase
  - Security: Ranger
  - Monitoring: Ambari Metrics, Grafana
  - And more...

- **Advanced Configuration**
  - Customizable cluster topology
  - External database integration
  - Security configuration (Kerberos, Ranger)
  - Resource management
  - Directory customization

## Quick Start

### Prerequisites

1. **System Requirements**
   - CentOS/Rocky Linux 8/9
   - Python 3.x
   - Ansible
   - Docker (for container-based deployment)

2. **Package Setup**
   ```bash
   # Install dependencies (CentOS/Rocky Linux)
   sh deploy_py/shell/utils/setup-env-centos.sh false
   
   # Setup Python environment
   source setup_pypath.sh
   ```

### Docker Deployment

1. **Configure deployment**
   ```bash
   cp conf/base_conf.yml.template conf/base_conf.yml
   ```

2. **Update configuration in `base_conf.yml`**
   ```yaml
   repo_pkgs_dir: "/path/to/ambari/packages"
   components_to_install: ["hbase","hdfs","yarn","hive","zookeeper","ambari"]
   docker_options:
     instance_num: 4
     memory_limit: "16g"
     components_port_map:
       AMBARI_SERVER: 8083
   ```

3. **Start deployment**
   ```bash
   python3 deploy_py/main.py -docker-deploy
   ```

### Bare Metal/VM Deployment

1. **Configure hosts**
   - Update `/etc/hosts` with cluster information
   - Configure SSH access
   - Disable firewall and SELinux

2. **Generate configuration**
   ```bash
   python3 deploy_py/main.py -generate-conf
   ```

3. **Start deployment**
   ```bash
   nohup python3 deploy_py/main.py -deploy &
   tail -f logs/ansible-playbook.log
   ```

## Documentation

### Core Documentation
- [Project Overview](docs/PROJECT_OVERVIEW.md) - Introduction, core features, and system components
- [Technical Architecture](docs/TECHNICAL_ARCHITECTURE.md) - Detailed system architecture and technical implementation
- [Code Architecture](docs/CODE_ARCHITECTURE.md) - Code structure, core components, and development guidelines

### Deployment Guides
- [Automated Deployment Guide](docs/automated-deployment.md) - Step-by-step deployment instructions
- [Advanced Deployment Guide](docs/advanced-deployment.md) - Advanced configurations and customizations

## Configuration Reference

### Basic Configuration (`base_conf.yml`)

```yaml
# Default password
default_password: 'your-secure-password'

# Data directories
data_dirs: ["/data/sdv1"]

# Component selection
components_to_install: ["hbase","hdfs","yarn","hive","zookeeper","ambari"]

# Cluster configuration
cluster_name: 'cluster'
hdfs_ha_name: 'ambari-cluster'
ambari_server_port: 8080

# Stack version
stack_version: '3.3.0'
```

### Advanced Features

- High Availability (HA) Setup
- External Database Integration
- Security Configuration
- Custom Directory Layout
- Resource Management
- Service Integration

## Access and Management

Access Ambari Web UI:
```
http://<ambari-server>:8080
Default credentials:
Username: admin
Password: <configured_password>
```

## Troubleshooting

Common issues and solutions:

1. **Ambari Agent Registration**
   - Verify hostname configuration
   - Check network connectivity
   - Validate agent logs

2. **Component Installation**
   - Verify package availability
   - Check disk space
   - Review service logs

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

This project is licensed under the Apache License 2.0.
