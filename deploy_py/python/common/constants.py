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

import os

PRJDIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../")
)
PRJ_BIN_DIR = os.path.join(PRJDIR, "bin")
CONF_DIR = os.path.join(PRJDIR, "conf")

CONF_NAME = "conf.yml"
BASE_CONF_NAME = "base_conf.yml"
HOSTS_CONF_NAME = "hosts_info.yml"
GET_CONF_TPL_NAME = lambda x: f"{x}.template"

SHELL_RELATIVE_PATH = "deploy_py/shell"
SHELL_UTILS_RELATIVE_PATH = "deploy_py/shell/utils"
SHELL_PATH = os.path.join(PRJDIR, SHELL_RELATIVE_PATH)
SHELL_UTILS_PATH = os.path.join(PRJDIR, SHELL_UTILS_RELATIVE_PATH)

ANSIBLE_PRJ_DIR = os.path.join(PRJDIR, "deploy_ansible/ansible-scripts")
BUILD_SCRIPT_RELATIVE_PATH = "deploy_py/python/build/bigtop_utils.py"
BUILD_SCRIPT = os.path.join(PRJDIR, BUILD_SCRIPT_RELATIVE_PATH)
BLUEPRINT_FILES_DIR = os.path.join(
    ANSIBLE_PRJ_DIR, "playbooks/roles/ambari-blueprint/files/"
)
CLUSTER_TEMPLATES_DIR = os.path.join(PRJDIR, "deploy_py/resources/cluster_templates")
PLUGINS_DIR = os.path.join(PRJDIR, "deploy_py/python/plugins")
OUTPUT_DIR = os.path.join(PRJDIR, "output/")
LOGS_DIR = os.path.join(PRJDIR, "logs")
PIP_CONF_FILE = os.path.join(
    PRJDIR, "deploy_py/python/build/templates/pip_conf/pip.conf"
)
PKG_RELATIVE_PATH = "deploy_py/resources/pkgs/"

TAR_FILE_PATH = os.path.join(PRJDIR, PKG_RELATIVE_PATH)
CI_TOOLS_MODULE_PATH = os.path.join(PRJDIR, "deploy_py/python")
REPO_FILES_DIR = os.path.join(PRJDIR, "deploy_py/resources/repo_info")
SUPPORTED_ARCHS = ["x86_64", "aarch64", "c86_64"]
SUPPORTED_OS = ["centos", "kylin", "openeuler"]

HTTPD_TPL_FILE = os.path.join(PRJDIR, "deploy_py/resources/templates/httpd.conf.tpl")
HTTPD_CONF_FILE = "/etc/httpd/conf/httpd.conf"
APACHE2_TPL_FILE = os.path.join(
    PRJDIR, "deploy_py/resources/templates/apache2.conf.tpl"
)
APACHE2_CONF_FILE = "/etc/apache2/sites-enabled/apache2.conf"

DEB_REPO_BASE_DIR = "/var/repos/apt"
DEB_DISTRIBUTION = "ubuntu"
DEB_CODENAME = "focal"

ALL_COMPONENTS = [
    "hadoop",
    "spark",
    "hive",
    "hbase",
    "zookeeper",
    "kafka",
    "flink",
    "ranger",
    "alluxio",
    "knox",
    "tez",
    "ambari",
    "ambari-infra",
    "ambari-metrics",
    "bigtop-select",
    "bigtop-jsvc",
    "bigtop-groovy",
    "bigtop-utils",
    "bigtop-ambari-mpack",
]

