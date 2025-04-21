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

from python.config_management.configurations.base_configuration import *
from python.config_management.dynamic_variable_generator import DynamicVariableGenerator


class AmbariClusterTemplateConfiguration(BaseConfiguration):
    def __init__(self, name, dynamic_variable_generator: DynamicVariableGenerator):
        self.dynamic_variable_generator = dynamic_variable_generator
        super().__init__(name)

    def get_rendered_advanced_conf(self):
        rendered_advanced_conf = self.dynamic_variable_generator.generate()
        return rendered_advanced_conf

    def generate_ambari_cluster_template(self):
        rendered_advanced_conf = self.get_rendered_advanced_conf()
        security = rendered_advanced_conf["security"]
        kerberos_admin_principal = f"{rendered_advanced_conf['security_options']['admin_principal']}@{rendered_advanced_conf['security_options']['realm']}"
        kerberos_admin_password = rendered_advanced_conf["security_options"][
            "admin_password"
        ]
        ambari_cluster_template_host_groups = []

        for group_name, group_hosts in rendered_advanced_conf["host_groups"].items():
            hosts = [{"fqdn": host} for host in group_hosts]
            ambari_cluster_template_host_groups.append(
                {"name": group_name, "hosts": hosts}
            )

        cluster_template = {
            "blueprint": rendered_advanced_conf["blueprint_name"],
            "config_recommendation_strategy": rendered_advanced_conf["ambari_options"][
                "config_recommendation_strategy"
            ],
            "default_password": rendered_advanced_conf["default_password"],
            "host_groups": ambari_cluster_template_host_groups,
        }

        if security and security == "mit-kdc":
            cluster_template["credentials"] = [
                {
                    "alias": "kdc.admin.credential",
                    "principal": kerberos_admin_principal,
                    "key": kerberos_admin_password,
                    "type": "TEMPORARY",
                }
            ]
            cluster_template["security"] = {"type": "KERBEROS"}
        self.conf = cluster_template

    def get_conf(self):
        self.generate_ambari_cluster_template()
        return self.conf

    def save(self):
        self.set_path(BLUEPRINT_FILES_DIR).set_format(FileManager.FileType.JSON)
        super().save()
