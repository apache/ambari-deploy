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

from python.config_management.service_map import *

from .validator import *


class ConfValidator(Validator):
    def __init__(self, base_conf):
        self.base_conf = base_conf
        super().__init__()

    def validate(self):
        if (
            self.base_conf.get("components_to_install") == None
            or len(self.base_conf.get("components_to_install")) == 0
        ):
            self.err_messages.append(
                "components_to_install property must be configured"
            )

        for com in self.base_conf.get("components_to_install"):
            if not ServiceMap.is_component_supported(com):
                self.err_messages.append(f"component '{com}' is not supported.")
        return self
