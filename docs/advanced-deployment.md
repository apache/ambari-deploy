# Advanced Deployment Configuration

This guide provides detailed instructions for advanced deployment scenarios and customizations of Apache Ambari and Hadoop ecosystem components.

## Configuration Workflow

When using non-Docker deployment with advanced configurations:

1. After modifying `conf/base_conf.yml`, always regenerate the advanced configuration:
   ```bash
   source setup_pypath.sh
   python3 deploy_py/main.py -generate-conf
   ```

2. Modify the generated `conf/conf.yml` according to your needs

3. Start deployment:
   ```bash
   nohup python3 deploy_py/main.py -deploy &
   tail -f logs/ansible-playbook.log
   ```

**Important Note**: Running `python3 deploy_py/main.py -generate-conf` again will overwrite your customized `conf/conf.yml`.

## Advanced Configuration Scenarios

### 1. Customizing Cluster Topology

The cluster topology is primarily controlled by two configuration sections in `conf.yml`: `host_groups` and `group_services`.

#### Host Groups Configuration
```yaml
host_groups:
  group0: [server0]
  group1: [server1]
  group2: [server2,server3]
```
Each group contains a set of hostnames that will be treated as a unit for service deployment.

#### Service Groups Configuration
```yaml
group_services:
  group0: [AMBARI_SERVER, NAMENODE, ZKFC, ...]
  group1: [NAMENODE, ZKFC, JOURNALNODE, ...]
  group2: [ZOOKEEPER_SERVER, JOURNALNODE, ...]
```

### 2. Component Reference Guide

Here's a comprehensive list of available components and their functions:

#### HDFS Components
- **NAMENODE** (HA capable)
  - Core component managing filesystem metadata
  - Deploy 2 instances for HA mode
- **DATANODE**
  - Stores actual data blocks
- **JOURNALNODE**
  - Required for HA: minimum 3 instances (odd number)
- **ZKFC**
  - Must be co-located with NAMENODE
  - Required for HA: 2 instances

#### YARN Components
- **RESOURCEMANAGER** (HA capable)
  - Central resource management
  - Deploy 2 instances for HA mode
- **NODEMANAGER**
  - Manages resources on individual nodes
- **HISTORYSERVER**
  - Stores job history
- **APP_TIMELINE_SERVER**
  - Application timeline tracking

#### HBase Components
- **HBASE_MASTER** (HA capable)
  - Cluster management and coordination
  - Deploy 2 instances for HA mode
- **HBASE_REGIONSERVER**
  - Data storage and management

#### Hive Components
- **HIVE_METASTORE**
  - Metadata storage
- **HIVE_SERVER** (HA capable)
  - Query processing
- **WEBHCAT_SERVER**
  - REST interface

#### Other Core Components
- **ZOOKEEPER_SERVER**
  - Must deploy odd number of instances
- **KAFKA_BROKER**
  - Message broker
- **SPARK_JOBHISTORYSERVER**
  - Spark job history
- **FLINK_HISTORYSERVER**
  - Flink job history

### 3. Using External Databases

To use external databases, you need to:

1. Create necessary users and databases manually:
   ```sql
   -- PostgreSQL example
   CREATE USER hive WITH PASSWORD 'hive';
   CREATE DATABASE hive OWNER hive;
   GRANT ALL PRIVILEGES ON DATABASE hive TO hive;

   CREATE USER ranger WITH PASSWORD 'ranger';
   CREATE DATABASE ranger OWNER ranger;
   GRANT ALL PRIVILEGES ON DATABASE ranger TO ranger;
   ```

2. Configure database settings in `conf.yml`:
   ```yaml
   database: 'postgres'
   database_options:
     external_hostname: 'your-db-host'
     hive_db_name: 'hive'
     hive_db_username: 'hive'
     hive_db_password: 'your-password'
     rangeradmin_db_name: 'ranger'
     rangeradmin_db_username: 'ranger'
     rangeradmin_db_password: 'your-password'
   ```

### 4. Customizing Directory Locations

You can customize various directory locations:

```yaml
data_dirs: ["/data/sdv1"]  # Base data directory

# HDFS directories
hdfs_dfs_namenode_name_dir: "{{ hadoop_base_dir }}/hdfs/namenode"
hdfs_dfs_datanode_data_dir: "{% for dr in data_dirs %}{{ dr }}/hadoop/hdfs/data{% if not loop.last %},{% endif %}{% endfor %}"

# YARN directories
yarn_nodemanager_local_dirs: "{{ hadoop_base_dir }}/yarn/local"
yarn_nodemanager_log_dirs: "{{ hadoop_base_dir }}/yarn/log"

# Other service directories
zookeeper_data_dir: "{{ hadoop_base_dir }}/zookeeper"
kafka_log_base_dir: "{% for dr in data_dirs %}{{ dr }}/kafka-logs{% if not loop.last %},{% endif %}{% endfor %}"
```

### 5. Enabling Ranger

To enable Ranger and its plugins:

```yaml
ranger_options:
  enable_plugins: yes

ranger_security_options:
  ranger_admin_password: "your-password"
  ranger_keyadmin_password: "your-password"
  kms_master_key_password: "your-password"
```

### 6. Customizing Ambari Configuration

Modify Ambari-specific settings:

```yaml
ambari_options:
  ambari_agent_run_user: 'ambari'
  ambari_server_run_user: 'ambari'
  ambari_admin_user: 'admin'
  ambari_admin_password: 'your-password'
  config_recommendation_strategy: 'ALWAYS_APPLY'
```

## Best Practices

1. **High Availability Setup**
   - Deploy NAMENODE, RESOURCEMANAGER, and HBASE_MASTER in pairs for HA
   - Use odd number of JOURNALNODE and ZOOKEEPER_SERVER instances
   - Co-locate ZKFC with NAMENODE

2. **Resource Planning**
   - Distribute memory-intensive services across nodes
   - Consider network topology when placing services
   - Plan for future scaling

3. **Security Considerations**
   - Use external databases for production
   - Enable Ranger for centralized security
   - Configure proper authentication mechanisms 

## Complete Configuration Reference

Below is a complete configuration example with detailed explanations for each section:

```yaml
############################
## Host Groups & Services ##
############################
# Define machine groups and their members
host_groups:
  group0: [e977d8bea74d.bigtop.apache.org]
  group1: [b76d76c80f15.bigtop.apache.org]
  group2: [8874239dee4b.bigtop.apache.org]

# Define which services run on which groups
group_services:
  group0: [AMBARI_SERVER, NAMENODE, ZKFC, JOURNALNODE, RESOURCEMANAGER, ZOOKEEPER_SERVER,
    HBASE_MASTER, HIVE_METASTORE, SPARK_THRIFTSERVER, FLINK_HISTORYSERVER, HISTORYSERVER,
    RANGER_TAGSYNC, RANGER_USERSYNC]
  group1: [NAMENODE, ZKFC, JOURNALNODE, RESOURCEMANAGER, ZOOKEEPER_SERVER, HBASE_MASTER,
    DATANODE, NODEMANAGER, APP_TIMELINE_SERVER, RANGER_ADMIN, METRICS_GRAFANA, SPARK_JOBHISTORYSERVER,
    INFRA_SOLR]
  group2: [ZOOKEEPER_SERVER, JOURNALNODE, DATANODE, NODEMANAGER, TIMELINE_READER,
    YARN_REGISTRY_DNS, METRICS_COLLECTOR, HBASE_REGIONSERVER, HIVE_SERVER, WEBHCAT_SERVER,
    INFRA_SOLR]

############################
## Basic Configuration    ##
############################
# Default password for all services
default_password: B767610qa4Z

# Data directories for all components
# Can specify multiple directories for HDFS DataNode storage
data_dirs: [/data/sdv1]

# Repository configuration
# Option 1: Use existing repository
repos: null
# Option 2: Use local package directory
repo_pkgs_dir: /data1/apache/ambari-3.0_pkgs

# Stack version for Ambari
stack_version: 3.3.0

# Cluster naming
cluster_name: cluster
hdfs_ha_name: ambari-cluster

# Network configuration
ansible_ssh_port: 22
ambari_server_port: 8083
http_repo_port: 8881

############################
## Docker Configuration   ##
############################
docker_options:
  # Minimum 3 instances required for HA
  instance_num: 3
  # Memory limit per container
  memory_limit: 8g
  # Enable local repository
  enable_local_repo: true
  # Port mappings for accessing services
  components_port_map: {AMBARI_SERVER: 8083}
  # Container distribution settings
  distro: {name: centos, version: 8}
  # Components to install in Docker environment
  components: [hbase, hdfs, yarn, hive, zookeeper, ambari, spark, flink, ranger, infra_solr,
    ambari_metrics]
  default_password: B767610qa4Z

############################
## Memory Configuration  ##
############################
# Component memory settings (in MB)
hbase_heapsize: 1024
hadoop_heapsize: 1024
hive_heapsize: 1024
infra_solr_memory: 1024
spark_daemon_memory: 1024
zookeeper_heapsize: 1024
yarn_heapsize: 1024
alluxio_memory: 1024

############################
## Repository Settings   ##
############################
skip_cluster_clear: true
local_repo_ipaddress: 172.30.0.3
create_http_repo_for_local_pkgs: false

############################
## Deployment Control    ##
############################
deploy_ambari_only: false
prepare_nodes_only: false
backup_old_repo: no
should_deploy_ambari_mpack: false

############################
## Database Configuration ##
############################
# Database type selection
database: 'postgres'                                      # Options: 'postgres', 'mysql'
postgres_port: 5432
mysql_port: 3306

# Database options for all components
database_options:
  # External database configuration
  repo_url: ''
  external_hostname: ''                                   # Empty for local database installation

  # Ambari database
  ambari_db_name: 'ambari'
  ambari_db_username: 'ambari'
  ambari_db_password: '{{ default_password }}'

  # Hive database
  hive_db_name: 'hive'
  hive_db_username: 'hive'
  hive_db_password: '{{ default_password }}'

  # Ranger databases
  rangeradmin_db_name: 'ranger'
  rangeradmin_db_username: 'ranger'
  rangeradmin_db_password: '{{ default_password }}'
  rangerkms_db_name: 'rangerkms'
  rangerkms_db_username: 'rangerkms'
  rangerkms_db_password: '{{ default_password }}'

  # Other component databases
  dolphin_db_name: 'dolphinscheduler'
  dolphin_db_username: 'dolphin'
  dolphin_db_password: '{{ default_password }}'

  superset_db_name: 'superset'
  superset_db_username: 'superset'
  superset_db_password: '{{ default_password }}'

  cloudbeaver_db_name: 'cloudbeaver'
  cloudbeaver_db_username: 'cloudbeaver'
  cloudbeaver_db_password: '{{ default_password }}'

  nightingale_db_name: 'nightingale'
  nightingale_db_username: 'n9e'
  nightingale_db_password: '{{ default_password }}'

############################
## Security Configuration ##
############################
# Security type
security: 'none'                                         # Options: 'none', 'mit-kdc'

# Kerberos security options
security_options:
  external_hostname: ''                                   # Empty for local KDC installation
  external_hostip: ''                                    # For /etc/hosts DNS lookup
  realm: 'MY-REALM.COM'
  admin_principal: 'admin/admin'                         # Kerberos admin principal
  admin_password: "{{ default_password }}"
  kdc_master_key: "{{ default_password }}"               # Only for 'mit-kdc'
  http_authentication: yes                               # Enable HTTP authentication
  manage_krb5_conf: yes                                  # Set to no for FreeIPA/IdM

############################
## Ambari Configuration  ##
############################
ambari_options:
  # Run users
  ambari_agent_run_user: 'ambari'
  ambari_server_run_user: 'ambari'
  # Admin user settings
  ambari_admin_user: 'admin'
  ambari_admin_password: '{{ default_password }}'
  ambari_admin_default_password: 'admin'
  # Configuration strategy
  config_recommendation_strategy: 'ALWAYS_APPLY'          # Options: 'NEVER_APPLY', 'ONLY_STACK_DEFAULTS_APPLY', 
                                                        # 'ALWAYS_APPLY', 'ALWAYS_APPLY_DONT_OVERRIDE_CUSTOM_VALUES'

############################
## Ranger Configuration  ##
############################
# Ranger plugin options
ranger_options:
  enable_plugins: no                                     # Enable plugins for installed services

# Ranger security settings
ranger_security_options:
  ranger_admin_password: "{{ default_password }}"        # Password for admin users
  ranger_keyadmin_password: "{{ default_password }}"     # Password for keyadmin (HDP3 only)
  kms_master_key_password: "{{ default_password }}"      # Master key encryption password

############################
## General Configuration ##
############################
# System settings
external_dns: yes                                        # Use existing DNS or update /etc/hosts
disable_firewall: yes                                    # Disable local firewall service
timezone: Asia/Shanghai

# NTP configuration
external_ntp_server_hostname: ''                         # Empty for local NTP server

# Additional settings
packages_need_install: []
registry_dns_bind_port: "54"
blueprint_name: 'blueprint'                              # Blueprint name in Ambari
wait: true                                              # Wait for cluster installation
wait_timeout: 60
accept_gpl: yes                                         # Accept GPL licenses

############################
## Directory Configuration##
############################
# Base directories
base_log_dir: "/var/log"
base_tmp_dir: "/tmp"

# Service data directories
kafka_log_base_dir: "{% for dr in data_dirs %}{{ dr }}/kafka-logs{% if not loop.last %},{% endif %}{% endfor %}"
ams_base_dir: "/var/lib"
ranger_audit_hdfs_filespool_base_dir: "{{ base_log_dir }}"
ranger_audit_solr_filespool_base_dir: "{{ base_log_dir }}"

# HDFS directories
hdfs_dfs_namenode_checkpoint_dir: "{{ hadoop_base_dir }}/hdfs/namesecondary"
hdfs_dfs_namenode_name_dir: "{{ hadoop_base_dir }}/hdfs/namenode"
hdfs_dfs_journalnode_edits_dir: "{{ hadoop_base_dir }}/hdfs/journalnode"
hdfs_dfs_datanode_data_dir: "{% for dr in data_dirs %}{{ dr }}/hadoop/hdfs/data{% if not loop.last %},{% endif %}{% endfor %}"

# YARN directories
yarn_nodemanager_local_dirs: "{{ hadoop_base_dir }}/yarn/local"
yarn_nodemanager_log_dirs: "{{ hadoop_base_dir }}/yarn/log"
yarn_timeline_leveldb_dir: "{{ hadoop_base_dir }}/yarn/timeline"

# Other service directories
zookeeper_data_dir: "{{ hadoop_base_dir }}/zookeeper"
infra_solr_datadir: "{{ hadoop_base_dir }}/ambari-infra-solr/data"
heap_dump_location: "{{ base_tmp_dir }}"
hive_downloaded_resources_dir: "{{ base_tmp_dir }}/hive/${hive.session.id}_resources"

# Temporary directories
ansible_tmp_dir: /tmp/ansible
```

## Configuration Notes

### Host Groups and Services

- Each service can be configured for high availability (HA):
  - **NAMENODE**: Deploy 2 instances for HA
  - **RESOURCEMANAGER**: Deploy 2 instances for HA
  - **HBASE_MASTER**: Deploy 2 instances for HA
  - **HIVE_SERVER**: Deploy multiple instances for HA
  - **ZOOKEEPER_SERVER**: Must deploy odd number of instances

### Database Configuration

When using external databases:
1. Create users and databases manually before deployment
2. Ensure database is accessible from all nodes
3. Configure connection details in `database_options`

### Directory Configuration

- `data_dirs`: Primary configuration for all data storage
  - First directory is used for logs and default paths
  - All directories are used for HDFS DataNode storage
  - Multiple directories improve I/O performance

### Security Configuration

- Kerberos setup requires proper DNS resolution
- Ranger plugins can be enabled for all compatible services
- HTTP authentication can be enabled for web UIs

### Memory Configuration

- All memory settings are in MB
- Configure based on available hardware
- Consider service co-location when setting values 