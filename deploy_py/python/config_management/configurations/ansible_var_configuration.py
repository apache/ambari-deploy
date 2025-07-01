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

from python.config_management.dynamic_variable_generator import DynamicVariableGenerator

from .base_configuration import *


class AnsibleVarConfiguration(BaseConfiguration):
    def __init__(self, name, dynamic_variable_generator: DynamicVariableGenerator):
        self.dynamic_variable_generator = dynamic_variable_generator
        super().__init__(name)

    def generate_ansible_variables_conf(self):
        rendered_advanced_conf = self.dynamic_variable_generator.generate()
        for key in ["host_groups", "group_services"]:
            rendered_advanced_conf.pop(key, None)

        self.set_conf(rendered_advanced_conf)

    def get_conf(self):
        self.generate_ansible_variables_conf()
        return self.conf

    def save(self):
        self.set_path(os.path.join(ANSIBLE_PRJ_DIR, "playbooks/group_vars")).set_format(
            FileManager.FileType.YAML
        )
        super().save()
